"""
Strategy generation flow — the first core agent capability.

Orchestrates: Tavily research → Fastino SLM → Neo4j storage.
Automatically checks for existing Lessons and uses refine_strategy()
instead of generate_strategy() when past corrections exist.
"""

from datetime import datetime, timezone

from services.neo4j_service import get_session
from services.tavily_service import research_market
from services.slm_service import generate_strategy, refine_strategy


def _get_latest_strategy_version() -> int:
    """Return the highest strategy version number, or 0 if none exist."""
    with get_session() as session:
        result = session.run(
            "MATCH (s:Strategy) RETURN max(s.version) AS max_ver"
        )
        record = result.single()
        return record["max_ver"] or 0


def _get_lessons() -> list[dict]:
    """Fetch all Lesson nodes from Neo4j."""
    with get_session() as session:
        result = session.run(
            "MATCH (l:Lesson) RETURN l.type AS type, l.details AS details "
            "ORDER BY l.timestamp"
        )
        return [{"type": r["type"], "details": r["details"]} for r in result]


def _store_strategy(strategy_data: dict, version: int, prev_version: int | None) -> dict:
    """
    Create a Strategy node in Neo4j. If prev_version is set, also create
    an EVOLVED_FROM relationship to the previous strategy.
    """
    with get_session() as session:
        result = session.run(
            """
            CREATE (s:Strategy {
                version: $version,
                icp: $icp,
                keywords: $keywords,
                competitors: $competitors,
                created_at: datetime($created_at)
            })
            RETURN s {.*} AS strategy
            """,
            version=version,
            icp=strategy_data["icp"],
            keywords=strategy_data.get("keywords", []),
            competitors=strategy_data.get("competitors", []),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        stored = result.single()["strategy"]

        if prev_version is not None:
            session.run(
                """
                MATCH (curr:Strategy {version: $curr_ver})
                MATCH (prev:Strategy {version: $prev_ver})
                MERGE (curr)-[:EVOLVED_FROM]->(prev)
                """,
                curr_ver=version,
                prev_ver=prev_version,
            )

    return stored


async def run_strategy_generation(product_description: str) -> dict:
    """
    Full strategy generation pipeline:
      1. Tavily market research
      2. Check Neo4j for past lessons
      3. SLM generates (or refines) ICP
      4. Store new Strategy node in Neo4j
      5. Return everything

    Returns:
        {
            "version": int,
            "strategy": {"icp": ..., "keywords": [...], "competitors": [...]},
            "market_research": {...},
            "lessons_used": [...],
            "evolved_from": int | None,
        }
    """
    market_research = await research_market(product_description)

    lessons = _get_lessons()
    prev_version = _get_latest_strategy_version()
    new_version = prev_version + 1

    if lessons:
        strategy_data = await refine_strategy(
            product_description, market_research, lessons
        )
        evolved_from = prev_version
    else:
        strategy_data = await generate_strategy(
            product_description, market_research
        )
        evolved_from = prev_version if prev_version > 0 else None

    _store_strategy(strategy_data, new_version, evolved_from)

    return {
        "version": new_version,
        "strategy": strategy_data,
        "market_research": market_research,
        "lessons_used": lessons,
        "evolved_from": evolved_from,
    }
