"""
Fastino Pioneer SLM service for Recurve AI.

Functions:
  generate_strategy  — product + market research → ICP JSON
  classify_lead      — product desc + trigger events + company context → Strike/Monitor/Disregard
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
# 2. Lead classification  (Strike / Monitor / Disregard)
# ---------------------------------------------------------------------------

VALID_CLASSIFICATIONS = {"Strike", "Monitor", "Disregard"}

_CLASSIFY_SYSTEM = """\
You are a lead qualification classifier for B2B sales.

Given a product/service description, recent trigger events, and company context, \
classify the lead into exactly one category:

- Strike: Strong fit with an urgent, time-bound trigger — pursue immediately.
- Monitor: Potential fit but no urgent trigger — watch for changes.
- Disregard: Poor fit — wrong industry, too small, or fundamentally misaligned.

Respond with ONLY the classification label (Strike, Monitor, or Disregard). \
No explanation, no punctuation — just the single word."""


def build_classification_prompt(
    product_description: str,
    trigger_events: str,
    company_context: str,
) -> str:
    """Format lead data into the text schema the fine-tuned model expects."""
    return (
        f"Product/Service Description: {product_description}\n"
        f"Trigger Events: {trigger_events}\n"
        f"Company Context: {company_context}"
    )


async def classify_lead(
    product_description: str,
    trigger_events: str,
    company_context: str,
) -> dict:
    """
    Classify a lead as Strike, Monitor, or Disregard.

    The input text matches the fine-tuned model's training format
    (see pioneer_eval_set_60.jsonl).

    Returns: {"classification": "Strike"|"Monitor"|"Disregard"}
    """
    user_prompt = build_classification_prompt(
        product_description, trigger_events, company_context,
    )
    raw = _call_pioneer(_CLASSIFY_SYSTEM, user_prompt, max_tokens=20)
    label = raw.strip().split()[0].strip(".,;:\"'")

    if label not in VALID_CLASSIFICATIONS:
        for valid in VALID_CLASSIFICATIONS:
            if valid.lower() in raw.lower():
                label = valid
                break
        else:
            label = "Monitor"

    return {"classification": label}


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
