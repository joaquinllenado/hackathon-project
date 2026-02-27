"""
Scout trigger flow — agent response to status change (e.g. competitor outage).

Fetches current strategy, drafts pivot email, broadcasts to WebSocket.
"""

from services.feed_manager import feed_manager
from services.neo4j_service import get_session
from services.slm_service import draft_pivot_email


def _get_latest_strategy() -> dict | None:
    """Fetch the latest Strategy node from Neo4j. Returns None if none exist."""
    with get_session() as session:
        result = session.run(
            """
            MATCH (s:Strategy)
            RETURN s.version AS version, s.icp AS icp, s.keywords AS keywords, s.competitors AS competitors
            ORDER BY s.version DESC
            LIMIT 1
            """
        )
        record = result.single()
        if record is None:
            return None
        return {
            "version": record["version"],
            "icp": record["icp"] or "",
            "keywords": record["keywords"] or [],
            "competitors": record["competitors"] or [],
        }


async def run_scout_trigger_flow(trigger_event: dict) -> None:
    """
    Handle scout status change: draft pivot email and broadcast.

    trigger_event: {"status": "critical_outage", "competitor": "DigitalOcean", ...}
    """
    strategy = _get_latest_strategy()
    if strategy is None:
        competitor = trigger_event.get("competitor", "Unknown")
        strategy = {
            "icp": "Companies affected by cloud provider outages",
            "keywords": ["cloud migration", "reliability"],
            "competitors": [competitor] if competitor else [],
        }

    company = {
        "name": "Affected Customer",
        "domain": "example.com",
        "tech_stack": [trigger_event.get("competitor", "cloud provider")],
        "employees": "mid-market",
        "funding": "growth",
    }

    email = await draft_pivot_email(company, trigger_event, strategy)

    await feed_manager.broadcast(
        "pivot_email_drafted",
        {
            "subject": email.get("subject", ""),
            "body": email.get("body", ""),
            "trigger": trigger_event,
        },
    )
