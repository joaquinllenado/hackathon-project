"""
Tavily-powered fact-checking and market research for Recurve AI.

fact_check_lead  — validates a company's claimed tech stack against live web data
research_market  — gathers competitive landscape for a product description
"""

import os
from tavily import TavilyClient

_client = None

TECH_KEYWORDS = [
    "python", "go", "golang", "rust", "java", "ruby", "php", "typescript",
    "javascript", "c#", ".net", "elixir", "scala", "kotlin", "swift",
    "postgres", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cockroachdb", "oracle", "sql server", "sqlite", "cassandra",
    "aws", "gcp", "google cloud", "azure", "digitalocean", "heroku",
    "fly.io", "render", "vercel", "cloudflare", "on-prem",
    "kubernetes", "docker", "nomad", "terraform", "ansible",
    "react", "vue", "angular", "next.js", "django", "fastapi", "rails",
    "spring", "express", "flask",
]


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return _client


def _extract_tech_mentions(text: str) -> list[str]:
    """Pull known technology names out of a block of text."""
    text_lower = text.lower()
    found = []
    for kw in TECH_KEYWORDS:
        if kw in text_lower:
            found.append(kw)
    # Normalize postgres variants
    if "postgresql" in found and "postgres" in found:
        found.remove("postgresql")
    if "golang" in found and "go" in found:
        found.remove("golang")
    return sorted(set(found))


async def fact_check_lead(
    company_name: str,
    claimed_tech_stack: list[str],
) -> dict:
    """
    Search the web for real evidence of a company's tech stack and compare
    against what we have stored.

    Returns:
        {
            "actual_tech":  ["postgres", "aws", ...],
            "sources":      [{"url": "...", "summary": "..."}, ...],
            "mismatch":     True/False,
            "mismatch_details": "claimed X but found Y" | None,
        }
    """
    client = _get_client()

    query = f"{company_name} engineering tech stack infrastructure 2026"
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
    )

    all_text = ""
    sources = []
    for result in response.get("results", []):
        snippet = result.get("content", "")
        all_text += " " + snippet
        sources.append({
            "url": result.get("url", ""),
            "summary": snippet[:300],
        })

    actual_tech = _extract_tech_mentions(all_text)

    claimed_normalized = {t.lower() for t in claimed_tech_stack}
    actual_set = set(actual_tech)

    # A mismatch means: key technologies in the claimed stack are NOT
    # confirmed by any web evidence, OR web evidence shows fundamentally
    # different tech (e.g. MongoDB instead of Postgres).
    db_techs = {
        "postgres", "postgresql", "mysql", "mongodb", "redis",
        "dynamodb", "cockroachdb", "oracle", "sql server", "cassandra",
        "elasticsearch", "sqlite",
    }
    claimed_dbs = claimed_normalized & db_techs
    actual_dbs = actual_set & db_techs

    mismatch = False
    mismatch_details = None

    if claimed_dbs and actual_dbs and not claimed_dbs & actual_dbs:
        mismatch = True
        mismatch_details = (
            f"Claimed DB: {', '.join(sorted(claimed_dbs))} — "
            f"but web evidence shows: {', '.join(sorted(actual_dbs))}"
        )
    elif actual_tech and len(claimed_normalized & actual_set) == 0:
        mismatch = True
        mismatch_details = (
            f"None of the claimed stack {sorted(claimed_normalized)} "
            f"found in web results. Found instead: {actual_tech}"
        )

    return {
        "actual_tech": actual_tech,
        "sources": sources,
        "mismatch": mismatch,
        "mismatch_details": mismatch_details,
    }


async def research_market(product_description: str) -> dict:
    """
    Given a product description, research the competitive landscape.

    Returns:
        {
            "competitors":       [{"name": "...", "url": "...", "summary": "..."}],
            "pricing_insights":  [...],
            "complaints":        [...],
        }
    """
    client = _get_client()

    comp_response = client.search(
        query=f"competitors to: {product_description}",
        search_depth="advanced",
        max_results=5,
    )
    competitors = [
        {
            "name": r.get("title", ""),
            "url": r.get("url", ""),
            "summary": r.get("content", "")[:300],
        }
        for r in comp_response.get("results", [])
    ]

    pricing_response = client.search(
        query=f"{product_description} pricing comparison 2026",
        search_depth="basic",
        max_results=3,
    )
    pricing_insights = [
        r.get("content", "")[:300]
        for r in pricing_response.get("results", [])
    ]

    complaints_response = client.search(
        query=f"{product_description} complaints problems switching 2026",
        search_depth="basic",
        max_results=3,
    )
    complaints = [
        r.get("content", "")[:300]
        for r in complaints_response.get("results", [])
    ]

    return {
        "competitors": competitors,
        "pricing_insights": pricing_insights,
        "complaints": complaints,
    }
