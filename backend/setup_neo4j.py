"""
Neo4j schema setup + synthetic seed data for Recurve AI.

Usage:
    python setup_neo4j.py              # create constraints + seed data (skip if data exists)
    python setup_neo4j.py --reset      # wipe everything, recreate constraints, reseed
    python setup_neo4j.py --seed-only  # just insert seed data (no constraint creation)
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from services.neo4j_service import get_session, close_driver


# ---------------------------------------------------------------------------
# Schema: constraints & indexes
# ---------------------------------------------------------------------------

CONSTRAINTS = [
    "CREATE CONSTRAINT strategy_version IF NOT EXISTS FOR (s:Strategy) REQUIRE s.version IS UNIQUE",
    "CREATE CONSTRAINT company_domain IF NOT EXISTS FOR (c:Company) REQUIRE c.domain IS UNIQUE",
    "CREATE CONSTRAINT lesson_id IF NOT EXISTS FOR (l:Lesson) REQUIRE l.lesson_id IS UNIQUE",
    "CREATE INDEX evidence_url IF NOT EXISTS FOR (e:Evidence) ON (e.source_url)",
]


def create_schema():
    with get_session() as session:
        for stmt in CONSTRAINTS:
            session.run(stmt)
    print("[+] Schema constraints and indexes created.")


# ---------------------------------------------------------------------------
# Synthetic seed data
# ---------------------------------------------------------------------------

SEED_CYPHER = """
// ── Strategy v1 (initial) ─────────────────────────────────────────────
CREATE (s1:Strategy {
  version: 1,
  product_description: 'Managed Postgres hosting platform that simplifies database operations, reduces cloud costs, and enables multi-cloud deployments for engineering teams.',
  icp: 'B2B SaaS companies with 20-200 engineers running self-managed Postgres on AWS',
  keywords: ['postgres', 'database migration', 'managed hosting', 'aws rds alternative'],
  competitors: ['PlanetScale', 'Neon', 'Supabase', 'AWS RDS'],
  created_at: datetime('2026-02-27T09:00:00Z')
})

// ── Strategy v2 (evolved after lessons) ───────────────────────────────
CREATE (s2:Strategy {
  version: 2,
  product_description: 'Managed Postgres hosting platform that simplifies database operations, reduces cloud costs, and enables multi-cloud deployments for engineering teams.',
  icp: 'Series A-C SaaS companies (50-500 employees) actively migrating off AWS to multi-cloud, using Postgres or compatible DBs',
  keywords: ['postgres', 'multi-cloud', 'database migration', 'cloud-agnostic', 'cost optimization'],
  competitors: ['PlanetScale', 'Neon', 'Supabase', 'CockroachDB', 'Timescale'],
  created_at: datetime('2026-02-27T10:30:00Z')
})

CREATE (s2)-[:EVOLVED_FROM]->(s1)

// ── Companies (good fits) ─────────────────────────────────────────────
// No classification at seed time — the SLM computes it on-the-fly during validation.
CREATE (c1:Company  {name: 'GitLab',             domain: 'gitlab.com',          tech_stack: ['Postgres', 'Kubernetes', 'GCP'],            employees: 2000, funding: 'Public'})
CREATE (c2:Company  {name: 'Sentry',             domain: 'sentry.io',           tech_stack: ['Python', 'Postgres', 'Kubernetes', 'AWS'],   employees: 700,  funding: 'Series E'})
CREATE (c3:Company  {name: 'LaunchDarkly',       domain: 'launchdarkly.com',    tech_stack: ['Go', 'Postgres', 'AWS', 'Terraform'],        employees: 650,  funding: 'Series D'})
CREATE (c4:Company  {name: 'Retool',             domain: 'retool.com',          tech_stack: ['TypeScript', 'Postgres', 'AWS'],             employees: 500,  funding: 'Series C'})
CREATE (c5:Company  {name: 'PostHog',            domain: 'posthog.com',         tech_stack: ['TypeScript', 'Postgres', 'Kubernetes'],      employees: 200,  funding: 'Series B'})
CREATE (c6:Company  {name: 'Vercel',             domain: 'vercel.com',          tech_stack: ['TypeScript', 'Postgres', 'Multi-cloud'],      employees: 500,  funding: 'Series D'})

// ── Companies (mismatches — drive lessons) ────────────────────────────
CREATE (c7:Company  {name: 'Plausible Analytics', domain: 'plausible.io',       tech_stack: ['Elixir', 'Postgres', 'DigitalOcean'],       employees: 20,  funding: 'Bootstrapped'})
CREATE (c8:Company  {name: 'Oracle',              domain: 'oracle.com',         tech_stack: ['Java', 'Oracle DB', 'On-prem'],              employees: 160000, funding: 'Public'})
CREATE (c9:Company  {name: 'Fathom Analytics',    domain: 'usefathom.com',      tech_stack: ['Go', 'Postgres', 'Single-region'],           employees: 15,  funding: 'Bootstrapped'})
CREATE (c10:Company {name: 'MongoDB',             domain: 'mongodb.com',        tech_stack: ['MongoDB', 'Atlas', 'Multi-cloud'],           employees: 6000, funding: 'Public'})

// ── More companies (expand dataset) ────────────────────────────────────
CREATE (c11:Company {name: 'Plaid',               domain: 'plaid.com',          tech_stack: ['Go', 'Postgres', 'AWS'],                      employees: 1000, funding: 'Series D'})
CREATE (c12:Company {name: 'Twilio Segment',      domain: 'segment.com',        tech_stack: ['TypeScript', 'Postgres', 'AWS'],              employees: 600,  funding: 'Acquired'})
CREATE (c13:Company {name: 'Fivetran',            domain: 'fivetran.com',       tech_stack: ['Java', 'Postgres', 'GCP', 'Kubernetes'],       employees: 1200, funding: 'Series D'})
CREATE (c14:Company {name: 'Databricks',          domain: 'databricks.com',     tech_stack: ['Spark', 'Kubernetes', 'AWS', 'Azure', 'GCP'], employees: 6000, funding: 'Late-stage'})
CREATE (c15:Company {name: 'Stripe',              domain: 'stripe.com',         tech_stack: ['Ruby', 'Java', 'Postgres', 'AWS'],             employees: 8000, funding: 'Private'})
CREATE (c16:Company {name: 'Cloudflare',          domain: 'cloudflare.com',     tech_stack: ['Rust', 'Go', 'Postgres', 'Multi-cloud'],       employees: 4000, funding: 'Public'})
CREATE (c17:Company {name: 'Airtable',            domain: 'airtable.com',       tech_stack: ['TypeScript', 'Postgres', 'AWS'],              employees: 1200, funding: 'Series F'})
CREATE (c18:Company {name: 'Notion',              domain: 'notion.so',          tech_stack: ['TypeScript', 'Postgres', 'AWS'],              employees: 800,  funding: 'Series C'})
CREATE (c19:Company {name: 'Mux',                 domain: 'mux.com',            tech_stack: ['Go', 'Postgres', 'AWS'],                      employees: 400,  funding: 'Series D'})
CREATE (c20:Company {name: 'Render',              domain: 'render.com',         tech_stack: ['Go', 'Postgres', 'AWS'],                      employees: 150,  funding: 'Series B'})

// ── Strategy targeting ────────────────────────────────────────────────
CREATE (s1)-[:TARGETS]->(c1)
CREATE (s1)-[:TARGETS]->(c3)
CREATE (s1)-[:TARGETS]->(c7)
CREATE (s1)-[:TARGETS]->(c8)
CREATE (s1)-[:TARGETS]->(c9)
CREATE (s1)-[:TARGETS]->(c10)
CREATE (s1)-[:TARGETS]->(c12)
CREATE (s1)-[:TARGETS]->(c14)

CREATE (s2)-[:TARGETS]->(c1)
CREATE (s2)-[:TARGETS]->(c2)
CREATE (s2)-[:TARGETS]->(c4)
CREATE (s2)-[:TARGETS]->(c5)
CREATE (s2)-[:TARGETS]->(c6)
CREATE (s2)-[:TARGETS]->(c11)
CREATE (s2)-[:TARGETS]->(c13)
CREATE (s2)-[:TARGETS]->(c17)
CREATE (s2)-[:TARGETS]->(c18)
CREATE (s2)-[:TARGETS]->(c19)
CREATE (s2)-[:TARGETS]->(c20)

// ── Evidence ──────────────────────────────────────────────────────────
CREATE (ev1:Evidence  {source_url: 'https://about.gitlab.com/handbook/engineering/',     summary: 'GitLab engineering/handbook landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:15:00Z')})
CREATE (ev2:Evidence  {source_url: 'https://sentry.io/about/',                          summary: 'Sentry public about page (used as baseline evidence URL for an established SaaS company).', retrieved_at: datetime('2026-02-27T09:18:00Z')})
CREATE (ev3:Evidence  {source_url: 'https://launchdarkly.com/blog/',                    summary: 'LaunchDarkly blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:20:00Z')})
CREATE (ev4:Evidence  {source_url: 'https://retool.com/blog/',                          summary: 'Retool blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:21:00Z')})
CREATE (ev5:Evidence  {source_url: 'https://posthog.com/blog',                          summary: 'PostHog blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:22:00Z')})
CREATE (ev6:Evidence  {source_url: 'https://vercel.com/blog',                           summary: 'Vercel blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:23:00Z')})
CREATE (ev7:Evidence  {source_url: 'https://plausible.io/blog',                         summary: 'Plausible blog landing page; used here to represent a real but smaller team/site with a minimal infra footprint.', retrieved_at: datetime('2026-02-27T09:24:00Z')})
CREATE (ev8:Evidence  {source_url: 'https://www.oracle.com/database/',                  summary: 'Oracle Database product page; used as evidence for legacy DB / enterprise focus (likely poor fit for this ICP).', retrieved_at: datetime('2026-02-27T09:25:00Z')})
CREATE (ev9:Evidence  {source_url: 'https://usefathom.com/blog',                        summary: 'Fathom blog landing page; used here to represent a real but small/bootstrapped company for mismatch cases.', retrieved_at: datetime('2026-02-27T09:26:00Z')})
CREATE (ev10:Evidence {source_url: 'https://www.mongodb.com/products/platform',         summary: 'MongoDB platform page; used as evidence for a primary MongoDB-first stack (tech mismatch for Postgres ICP).', retrieved_at: datetime('2026-02-27T09:27:00Z')})
CREATE (ev11:Evidence {source_url: 'https://plaid.com/blog/',                           summary: 'Plaid blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:28:00Z')})
CREATE (ev12:Evidence {source_url: 'https://segment.com/blog/',                         summary: 'Segment blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:29:00Z')})
CREATE (ev13:Evidence {source_url: 'https://www.fivetran.com/blog',                     summary: 'Fivetran blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:30:00Z')})
CREATE (ev14:Evidence {source_url: 'https://www.databricks.com/blog',                   summary: 'Databricks blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:31:00Z')})
CREATE (ev15:Evidence {source_url: 'https://stripe.com/blog',                           summary: 'Stripe blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:32:00Z')})
CREATE (ev16:Evidence {source_url: 'https://blog.cloudflare.com/',                      summary: 'Cloudflare blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:33:00Z')})
CREATE (ev17:Evidence {source_url: 'https://airtable.com/blog',                         summary: 'Airtable blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:34:00Z')})
CREATE (ev18:Evidence {source_url: 'https://www.notion.so/blog',                        summary: 'Notion blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:35:00Z')})
CREATE (ev19:Evidence {source_url: 'https://mux.com/blog',                              summary: 'Mux blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:36:00Z')})
CREATE (ev20:Evidence {source_url: 'https://render.com/blog',                           summary: 'Render blog landing page (public footprint used for synthetic evidence).', retrieved_at: datetime('2026-02-27T09:37:00Z')})

CREATE (c1)-[:HAS_EVIDENCE]->(ev1)
CREATE (c2)-[:HAS_EVIDENCE]->(ev2)
CREATE (c3)-[:HAS_EVIDENCE]->(ev3)
CREATE (c4)-[:HAS_EVIDENCE]->(ev4)
CREATE (c5)-[:HAS_EVIDENCE]->(ev5)
CREATE (c6)-[:HAS_EVIDENCE]->(ev6)
CREATE (c7)-[:HAS_EVIDENCE]->(ev7)
CREATE (c8)-[:HAS_EVIDENCE]->(ev8)
CREATE (c9)-[:HAS_EVIDENCE]->(ev9)
CREATE (c10)-[:HAS_EVIDENCE]->(ev10)
CREATE (c11)-[:HAS_EVIDENCE]->(ev11)
CREATE (c12)-[:HAS_EVIDENCE]->(ev12)
CREATE (c13)-[:HAS_EVIDENCE]->(ev13)
CREATE (c14)-[:HAS_EVIDENCE]->(ev14)
CREATE (c15)-[:HAS_EVIDENCE]->(ev15)
CREATE (c16)-[:HAS_EVIDENCE]->(ev16)
CREATE (c17)-[:HAS_EVIDENCE]->(ev17)
CREATE (c18)-[:HAS_EVIDENCE]->(ev18)
CREATE (c19)-[:HAS_EVIDENCE]->(ev19)
CREATE (c20)-[:HAS_EVIDENCE]->(ev20)

// ── Lessons (self-corrections) ────────────────────────────────────────
CREATE (les1:Lesson {lesson_id: 'les-001', type: 'CompanyTooSmall',    details: 'Plausible Analytics appears to be a small/lean team; despite being real and reputable, it is below the ICP size/complexity threshold for this synthetic dataset.', timestamp: datetime('2026-02-27T09:35:00Z')})
CREATE (les2:Lesson {lesson_id: 'les-002', type: 'ContractLockIn',     details: 'Oracle represents an enterprise/legacy vendor profile with long procurement cycles and existing vendor commitments; not a realistic target for a mid-market Postgres migration motion.', timestamp: datetime('2026-02-27T09:36:00Z')})
CREATE (les3:Lesson {lesson_id: 'les-003', type: 'CompanyTooSmall',    details: 'Fathom Analytics is a small/bootstrapped team; infra footprint is likely too small to justify a heavy migration/managed hosting initiative.', timestamp: datetime('2026-02-27T09:37:00Z')})
CREATE (les4:Lesson {lesson_id: 'les-004', type: 'TechStackMismatch',  details: 'MongoDB is strongly associated with a MongoDB-first stack; initial keyword matches can be misleading for a Postgres-focused ICP.', timestamp: datetime('2026-02-27T09:38:00Z')})
CREATE (les5:Lesson {lesson_id: 'les-005', type: 'SegmentPivot',       details: 'Over 60% of v1 leads failed validation. ICP was too broad — pivoting to mid-market companies actively migrating to multi-cloud.', timestamp: datetime('2026-02-27T10:00:00Z')})

CREATE (c7)-[:LEARNED_FROM]->(les1)
CREATE (c8)-[:LEARNED_FROM]->(les2)
CREATE (c9)-[:LEARNED_FROM]->(les3)
CREATE (c10)-[:LEARNED_FROM]->(les4)
CREATE (s2)-[:LEARNED_FROM]->(les5)
"""


def seed_data():
    with get_session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS cnt")
        count = result.single()["cnt"]
        if count > 0:
            print(f"[!] Database already has {count} nodes. Use --reset to wipe and reseed.")
            return False
        session.run(SEED_CYPHER)
    print("[+] Synthetic seed data inserted (2 strategies, 20 companies, 20 evidence, 5 lessons).")
    return True


def reset():
    with get_session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("[!] All nodes and relationships deleted.")


def verify():
    with get_session() as session:
        result = session.run(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC"
        )
        print("\n[=] Current graph contents:")
        for record in result:
            print(f"    {record['label']}: {record['cnt']}")

        result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC"
        )
        print("\n[=] Relationships:")
        for record in result:
            print(f"    {record['rel']}: {record['cnt']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Neo4j setup for Recurve AI")
    parser.add_argument("--reset", action="store_true", help="Wipe all data before setup")
    parser.add_argument("--seed-only", action="store_true", help="Only insert seed data (skip constraints)")
    args = parser.parse_args()

    try:
        if args.reset:
            reset()

        if not args.seed_only:
            create_schema()

        seed_data()
        verify()
    finally:
        close_driver()


if __name__ == "__main__":
    main()
