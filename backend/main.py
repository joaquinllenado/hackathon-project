import asyncio
import hashlib
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from services.modulate_service import transcribe_audio
from services.feed_manager import feed_manager
from services.neo4j_service import get_session
from agent.strategy import run_strategy_generation
from agent.validation import run_validation_loop
from agent.pivot import run_pivot_drafting
from workers.scout import run_scout_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    scout_task = None
    if os.environ.get("SCOUT_TARGET_URL", "").strip():
        scout_task = asyncio.create_task(run_scout_loop())
    yield
    if scout_task is not None:
        scout_task.cancel()
        try:
            await scout_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MAX_DESCRIPTION_LENGTH = 10_000


class ProductInput(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("description must not be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_max_length(cls, v: str) -> str:
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"description must not exceed {MAX_DESCRIPTION_LENGTH} characters")
        return v


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!"}


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    result = await transcribe_audio(file)
    return result


@app.post("/api/product")
async def ingest_product(payload: ProductInput):
    result = await run_strategy_generation(payload.description)
    return result


@app.post("/api/validate")
async def validate_leads(strategy_version: int | None = None):
    result = await run_validation_loop(strategy_version)
    return result


class TriggerInput(BaseModel):
    status: str = "critical_outage"
    competitor: str = "DigitalOcean"


@app.post("/api/mock-trigger")
async def mock_trigger(payload: TriggerInput):
    result = await run_pivot_drafting(payload.model_dump())
    if "error" not in result:
        await feed_manager.broadcast(
            "mock_trigger_response",
            {"trigger": payload.model_dump(), "result": result},
        )
    return result


def _serialize_value(v):
    """Convert Neo4j datetime and other types to JSON-serializable form."""
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


@app.get("/api/strategy")
def get_strategy():
    try:
        with get_session() as session:
            result = session.run(
                "MATCH (s:Strategy) RETURN s {.*} AS strategy "
                "ORDER BY s.version DESC LIMIT 1"
            )
            record = result.single()
            if record is None:
                return {"strategy": None}
            strategy = dict(record["strategy"])
            strategy = {k: _serialize_value(v) for k, v in strategy.items()}
            return {"strategy": strategy}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {e}") from e


@app.get("/api/leads")
def get_leads(strategy_version: int | None = None):
    """Return leads ordered by classification: Strike → Monitor → Disregard → unclassified."""
    _ORDER = """
        ORDER BY
          CASE c.classification
            WHEN 'Strike'    THEN 0
            WHEN 'Monitor'   THEN 1
            WHEN 'Disregard' THEN 2
            ELSE 3
          END, c.name
    """
    try:
        with get_session() as session:
            if strategy_version is not None:
                result = session.run(
                    f"""
                    MATCH (s:Strategy {{version: $version}})-[:TARGETS]->(c:Company)
                    RETURN c {{.*}} AS company
                    {_ORDER}
                    """,
                    version=strategy_version,
                )
            else:
                result = session.run(
                    f"""
                    MATCH (s:Strategy)-[:TARGETS]->(c:Company)
                    WITH max(s.version) AS latest
                    MATCH (s:Strategy {{version: latest}})-[:TARGETS]->(c:Company)
                    RETURN c {{.*}} AS company
                    {_ORDER}
                    """
                )
            leads = [dict(r["company"]) for r in result]
            for lead in leads:
                lead.update({k: _serialize_value(v) for k, v in lead.items()})
            return {"leads": leads}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {e}") from e


@app.get("/api/lessons")
def get_lessons():
    try:
        with get_session() as session:
            result = session.run(
                "MATCH (l:Lesson) RETURN l {.*} AS lesson "
                "ORDER BY l.timestamp DESC"
            )
            lessons = [dict(r["lesson"]) for r in result]
            for lesson in lessons:
                lesson.update({k: _serialize_value(v) for k, v in lesson.items()})
            return {"lessons": lessons}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {e}") from e


def _node_id(label: str, key: str | int) -> str:
    return f"{label.lower()}-{key}"


@app.get("/api/graph")
def get_graph():
    """Return Neo4j subgraph as { nodes, links } for react-force-graph / vis-network."""
    try:
        with get_session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE n:Strategy OR n:Company OR n:Evidence OR n:Lesson
                OPTIONAL MATCH (n)-[r]->(m)
                WHERE m:Strategy OR m:Company OR m:Evidence OR m:Lesson
                RETURN n, type(r) AS rel_type, m
                """
            )
            nodes_seen: dict[str, dict] = {}
            links: list[dict] = []

            for record in result:
                n = record["n"]
                if n is None:
                    continue
                labels = list(n.labels)
                props = dict(n)

                if "Strategy" in labels:
                    nid = _node_id("strategy", props.get("version", id(n)))
                    nodes_seen[nid] = {
                        "id": nid,
                        "label": f"Strategy v{props.get('version', '?')}",
                        "type": "strategy",
                        **{k: _serialize_value(v) for k, v in props.items()},
                    }
                elif "Company" in labels:
                    nid = _node_id("company", props.get("domain", id(n)))
                    nodes_seen[nid] = {
                        "id": nid,
                        "label": props.get("name", props.get("domain", "?")),
                        "type": "company",
                        **{k: _serialize_value(v) for k, v in props.items()},
                    }
                elif "Evidence" in labels:
                    url = props.get("source_url", str(id(n)))
                    nid = _node_id("evidence", hashlib.md5(url.encode()).hexdigest()[:12])
                    nodes_seen[nid] = {
                        "id": nid,
                        "label": url[:50] + "..." if len(url) > 50 else url,
                        "type": "evidence",
                        **{k: _serialize_value(v) for k, v in props.items()},
                    }
                elif "Lesson" in labels:
                    nid = _node_id("lesson", props.get("lesson_id", id(n)))
                    nodes_seen[nid] = {
                        "id": nid,
                        "label": props.get("type", "Lesson"),
                        "type": "lesson",
                        **{k: _serialize_value(v) for k, v in props.items()},
                    }
                else:
                    continue

                m = record["m"]
                rel = record["rel_type"]
                if m is not None and rel:
                    m_labels = list(m.labels)
                    m_props = dict(m)
                    if "Strategy" in m_labels:
                        mid = _node_id("strategy", m_props.get("version", id(m)))
                    elif "Company" in m_labels:
                        mid = _node_id("company", m_props.get("domain", id(m)))
                    elif "Evidence" in m_labels:
                        url = m_props.get("source_url", str(id(m)))
                        mid = _node_id("evidence", hashlib.md5(url.encode()).hexdigest()[:12])
                    elif "Lesson" in m_labels:
                        mid = _node_id("lesson", m_props.get("lesson_id", id(m)))
                    else:
                        continue
                    if mid not in nodes_seen:
                        if "Strategy" in m_labels:
                            nodes_seen[mid] = {
                                "id": mid,
                                "label": f"Strategy v{m_props.get('version', '?')}",
                                "type": "strategy",
                                **{k: _serialize_value(v) for k, v in m_props.items()},
                            }
                        elif "Company" in m_labels:
                            nodes_seen[mid] = {
                                "id": mid,
                                "label": m_props.get("name", m_props.get("domain", "?")),
                                "type": "company",
                                **{k: _serialize_value(v) for k, v in m_props.items()},
                            }
                        elif "Evidence" in m_labels:
                            url = m_props.get("source_url", str(id(m)))
                            nodes_seen[mid] = {
                                "id": mid,
                                "label": url[:50] + "..." if len(url) > 50 else url,
                                "type": "evidence",
                                **{k: _serialize_value(v) for k, v in m_props.items()},
                            }
                        elif "Lesson" in m_labels:
                            nodes_seen[mid] = {
                                "id": mid,
                                "label": m_props.get("type", "Lesson"),
                                "type": "lesson",
                                **{k: _serialize_value(v) for k, v in m_props.items()},
                            }
                    links.append({"source": nid, "target": mid, "type": rel})

            return {"nodes": list(nodes_seen.values()), "links": links}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {e}") from e


@app.post("/api/reset")
async def reset_graph():
    """Wipe all nodes and relationships from Neo4j so the agent starts fresh."""
    try:
        with get_session() as session:
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()
            deleted = summary.counters.nodes_deleted
        await feed_manager.broadcast(
            "graph_reset",
            {"nodes_deleted": deleted, "status": "All data cleared"},
        )
        return {"deleted_nodes": deleted}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {e}") from e


@app.websocket("/api/ws/feed")
async def ws_feed(websocket: WebSocket):
    await feed_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        feed_manager.disconnect(websocket)
