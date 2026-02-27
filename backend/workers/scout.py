"""
Yutori Scout background worker.

Polls SCOUT_TARGET_URL every SCOUT_POLL_INTERVAL seconds.
On status change, pushes event to WebSocket feed and triggers agent pivot flow.
"""

import asyncio
import json
import logging
import os

import httpx

from agent.scout_trigger import run_scout_trigger_flow
from services.feed_manager import feed_manager

logger = logging.getLogger(__name__)

_scout_task: asyncio.Task | None = None


def _parse_status_payload(data: dict) -> dict | None:
    """
    Extract status-related fields from the mock status page JSON.
    Expects {"status": "...", "competitor": "..."} per README.
    """
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    if status is None:
        return None
    return {
        "status": str(status),
        "competitor": str(data.get("competitor", "")),
        **{k: v for k, v in data.items() if k not in ("status", "competitor")},
    }


async def run_scout_loop() -> None:
    """
    Poll SCOUT_TARGET_URL every SCOUT_POLL_INTERVAL seconds.
    On status change, broadcast to WebSocket and trigger pivot flow.
    """
    url = os.environ.get("SCOUT_TARGET_URL", "").strip()
    interval = int(os.environ.get("SCOUT_POLL_INTERVAL", "10"))

    if not url:
        logger.info("SCOUT_TARGET_URL not set — scout worker disabled")
        return

    logger.info("Scout worker starting: url=%s, interval=%ds", url, interval)
    last_snapshot: dict | None = None

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                snapshot = _parse_status_payload(data)
                if snapshot is None:
                    logger.warning("Scout: invalid response shape at %s", url)
                    await asyncio.sleep(interval)
                    continue

                if last_snapshot is not None:
                    if snapshot.get("status") != last_snapshot.get("status"):
                        trigger_event = {**snapshot}
                        await feed_manager.broadcast(
                            "scout_status_change",
                            {
                                "prev": last_snapshot,
                                "current": snapshot,
                                "trigger_event": trigger_event,
                            },
                        )
                        try:
                            await run_scout_trigger_flow(trigger_event)
                        except Exception as e:
                            logger.exception("Scout trigger flow failed: %s", e)
                            await feed_manager.broadcast(
                                "agent_error",
                                {"error": str(e), "status": "Pivot email draft failed"},
                            )

                last_snapshot = snapshot

            except httpx.HTTPError as e:
                logger.warning("Scout HTTP error: %s", e)
            except json.JSONDecodeError as e:
                logger.warning("Scout JSON parse error: %s", e)
            except Exception as e:
                logger.exception("Scout loop error: %s", e)

            await asyncio.sleep(interval)
