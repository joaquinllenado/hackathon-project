"""
Strategy generation flow — the first core agent capability.

Orchestrates: Tavily research → Fastino SLM → Neo4j storage.
Automatically checks for existing Lessons and uses refine_strategy()
instead of generate_strategy() when past corrections exist.
"""

from datetime import datetime, timezone

from services.feed_manager import feed_manager
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


def _store_strategy(
    strategy_data: dict,
    product_description: str,
    version: int,
    prev_version: int | None,
) -> dict:
    """
    Create a Strategy node in Neo4j. If prev_version is set, also create
    an EVOLVED_FROM relationship to the previous strategy.
    """
    with get_session() as session:
        result = session.run(
            """
            CREATE (s:Strategy {
                version: $version,
                product_description: $product_description,
                icp: $icp,
                keywords: $keywords,
                competitors: $competitors,
                created_at: datetime($created_at)
            })
            RETURN s {.*} AS strategy
            """,
            version=version,
            product_description=product_description,
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
    try:
        await feed_manager.broadcast(
            "product_received",
            {"description_preview": product_description[:200] + ("..." if len(product_description) > 200 else "")},
        )

        await feed_manager.broadcast("market_research_started", {"status": "Searching market..."})
        market_research = await research_market(product_description)
        await feed_manager.broadcast(
            "market_research_done",
            {
                "competitors_count": len(market_research.get("competitors", [])),
                "status": "Market research complete",
            },
        )

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

        icp = strategy_data.get("icp") or ""
        icp_preview = icp[:150] + ("..." if len(icp) > 150 else "")
        await feed_manager.broadcast(
            "strategy_generated",
            {"icp_preview": icp_preview},
        )

        _store_strategy(strategy_data, product_description, new_version, evolved_from)

        await feed_manager.broadcast(
            "strategy_stored",
            {
                "version": new_version,
                "icp_preview": (icp[:100] + ("..." if len(icp) > 100 else "")),
                "status": f"Strategy v{new_version} stored",
            },
        )

        return {
            "version": new_version,
            "strategy": strategy_data,
            "market_research": market_research,
            "lessons_used": lessons,
            "evolved_from": evolved_from,
        }
    except Exception as e:
        await feed_manager.broadcast(
            "agent_error",
            {"error": str(e), "status": "Strategy generation failed"},
        )
        raise
