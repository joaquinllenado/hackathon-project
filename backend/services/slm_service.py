"""
Fastino Pioneer SLM service for The Recursive Hunter.

Functions:
  generate_strategy  — product + market research → ICP JSON
  score_lead         — company data + evidence → score 0-100 + reasoning
  refine_strategy    — previous strategy + lessons → evolved ICP JSON
  draft_pivot_email  — company + trigger event → outreach email
"""

import json
import os

import requests

PIONEER_URL = "https://api.pioneer.ai/inference"
MODEL_ID = "base:Qwen/Qwen3-8B"


def _call_pioneer(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Low-level call to the Fastino Pioneer API. Returns raw text response."""
    api_key = os.environ["FASTINO_PIONEER_API_KEY"]
    resp = requests.post(
        PIONEER_URL,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        json={
            "model_id": MODEL_ID,
            "task": "generate",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    if "completion" in data:
        return data["completion"]
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    if "output" in data:
        return data["output"]
    if "generated_text" in data:
        return data["generated_text"]
    return json.dumps(data)


def _parse_json_from_response(text: str) -> dict:
    """Extract JSON from an LLM response that may contain markdown fences."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
        text = text.split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1]
        text = text.split("```", 1)[0]
    return json.loads(text.strip())


# ---------------------------------------------------------------------------
# 1. Strategy generation
# ---------------------------------------------------------------------------

_STRATEGY_SYSTEM = """\
You are an expert B2B sales strategist. Given a product description and market \
research data, produce a precise Ideal Customer Profile (ICP) and targeting strategy.

Respond ONLY with valid JSON in this exact schema:
{
  "icp": "<one-paragraph description of ideal customer>",
  "keywords": ["<search keyword>", ...],
  "competitors": ["<competitor name>", ...]
}
No explanation, no markdown — just the JSON object."""

_STRATEGY_WITH_LESSONS_SYSTEM = """\
You are an expert B2B sales strategist improving your targeting based on past mistakes.

You will receive:
1. A product description
2. Market research
3. Lessons from previous failed lead validations

Use the lessons to REFINE and NARROW the ICP. Avoid repeating past mistakes.

Respond ONLY with valid JSON:
{
  "icp": "<improved one-paragraph ICP>",
  "keywords": ["<refined keyword>", ...],
  "competitors": ["<competitor name>", ...]
}
No explanation, no markdown — just the JSON object."""


async def generate_strategy(
    product_description: str,
    market_research: dict,
) -> dict:
    """
    Generate an initial ICP + strategy from a product description and
    Tavily market research.

    Returns: {"icp": "...", "keywords": [...], "competitors": [...]}
    """
    user_prompt = (
        f"Product: {product_description}\n\n"
        f"Market research:\n{json.dumps(market_research, indent=2)}"
    )
    raw = _call_pioneer(_STRATEGY_SYSTEM, user_prompt, max_tokens=1000)
    return _parse_json_from_response(raw)


async def refine_strategy(
    product_description: str,
    market_research: dict,
    lessons: list[dict],
) -> dict:
    """
    Generate an evolved strategy that incorporates past lessons.

    lessons: list of {"type": "...", "details": "..."} from Lesson nodes.
    Returns: {"icp": "...", "keywords": [...], "competitors": [...]}
    """
    lessons_text = "\n".join(
        f"- [{l['type']}] {l['details']}" for l in lessons
    )
    user_prompt = (
        f"Product: {product_description}\n\n"
        f"Market research:\n{json.dumps(market_research, indent=2)}\n\n"
        f"Lessons from previous rounds:\n{lessons_text}"
    )
    raw = _call_pioneer(_STRATEGY_WITH_LESSONS_SYSTEM, user_prompt, max_tokens=1000)
    return _parse_json_from_response(raw)


# ---------------------------------------------------------------------------
# 2. Lead scoring
# ---------------------------------------------------------------------------

_SCORE_SYSTEM = """\
You are a lead qualification analyst. Given a company profile, web evidence about \
them, and the current Ideal Customer Profile, score how well this lead fits.

Respond ONLY with valid JSON:
{
  "score": <integer 0-100>,
  "reasoning": "<2-3 sentences explaining the score>",
  "mismatch_type": "<null or one of: TechStackMismatch, CompanyTooSmall, ContractLockIn, SegmentPivot>",
  "mismatch_details": "<null or explanation of why this is a bad fit>"
}
No explanation outside the JSON."""


async def score_lead(
    company: dict,
    evidence: dict,
    icp: str,
) -> dict:
    """
    Score a lead 0-100 based on company data, web evidence, and current ICP.

    company:  {"name", "domain", "tech_stack", "employees", "funding"}
    evidence: output from fact_check_lead()
    icp:      the current ICP string from the Strategy node

    Returns: {"score": int, "reasoning": str, "mismatch_type": str|None, "mismatch_details": str|None}
    """
    user_prompt = (
        f"ICP: {icp}\n\n"
        f"Company: {json.dumps(company, indent=2)}\n\n"
        f"Web evidence (from Tavily):\n"
        f"  Actual tech found: {evidence.get('actual_tech', [])}\n"
        f"  Mismatch detected: {evidence.get('mismatch', False)}\n"
        f"  Details: {evidence.get('mismatch_details', 'None')}\n"
        f"  Sources: {json.dumps(evidence.get('sources', []), indent=2)}"
    )
    raw = _call_pioneer(_SCORE_SYSTEM, user_prompt, max_tokens=500)
    return _parse_json_from_response(raw)


# ---------------------------------------------------------------------------
# 3. Pivot email drafting
# ---------------------------------------------------------------------------

_PIVOT_EMAIL_SYSTEM = """\
You are a senior SDR writing a timely, context-aware outreach email.

A competitor has just experienced an outage or major issue. You need to draft a \
short, empathetic email to a potential customer who may be affected.

Rules:
- Keep it under 150 words
- Be empathetic, not predatory
- Reference the specific event
- Offer a concrete next step (demo, call, migration guide)

Respond ONLY with valid JSON:
{
  "subject": "<email subject line>",
  "body": "<full email body>"
}
No explanation outside the JSON."""


async def draft_pivot_email(
    company: dict,
    trigger_event: dict,
    strategy: dict,
) -> dict:
    """
    Draft a context-aware outreach email based on a trigger event
    (e.g. competitor outage).

    company:       {"name", "domain", "tech_stack", ...}
    trigger_event: {"status": "critical_outage", "competitor": "DigitalOcean", ...}
    strategy:      current Strategy node data

    Returns: {"subject": "...", "body": "..."}
    """
    user_prompt = (
        f"Trigger event: {json.dumps(trigger_event, indent=2)}\n\n"
        f"Target company: {json.dumps(company, indent=2)}\n\n"
        f"Our product ICP: {strategy.get('icp', '')}\n"
        f"Our keywords: {strategy.get('keywords', [])}"
    )
    raw = _call_pioneer(_PIVOT_EMAIL_SYSTEM, user_prompt, max_tokens=500)
    return _parse_json_from_response(raw)
