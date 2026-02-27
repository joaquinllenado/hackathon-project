# The Recursive Hunter

A self-improving autonomous SDR (Sales Development Rep) agent that generates sales strategy, finds leads, validates them, and learns from its mistakes — all from a single product description.

## What It Does

1. **Strategy Generation** — Given a product description (voice or text), the agent uses an SLM + web research to generate an Ideal Customer Profile (ICP), target keywords, and competitor landscape.
2. **Lead Discovery & Validation** — Finds leads matching the ICP, then fact-checks each one with live web data (Tavily). If a lead's tech stack or situation doesn't match, the agent logs a correction.
3. **Self-Improvement Loop** — Corrections are stored as "Lesson" nodes in Neo4j. On the next cycle, the agent reads its own lessons and refines its strategy and search criteria autonomously.
4. **Trigger-Based Pivots** — A background scout monitors external signals (competitor outages, price changes). When a trigger fires, the agent drafts context-aware outreach in real time.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    React Frontend                     │
│  - Product description input (text + voice/Modulate) │
│  - Live agent log / activity feed                    │
│  - Neo4j graph visualization ("Hunter's Brain")      │
│  - Strategy evolution timeline                       │
└──────────────┬───────────────────────────────────────┘
               │ /api/*
┌──────────────▼───────────────────────────────────────┐
│                  FastAPI Backend                       │
│                                                       │
│  POST /api/product    — Ingest product description    │
│  GET  /api/strategy   — Current ICP & strategy        │
│  GET  /api/leads      — Scored lead list              │
│  GET  /api/lessons    — Self-correction log           │
│  GET  /api/graph      — Neo4j subgraph for viz        │
│  POST /api/mock-trigger — Simulate a scout alert      │
│  WS   /api/ws/feed    — Real-time agent activity      │
│                                                       │
│  Background Workers:                                  │
│    - Scout (polls target URL for status changes)      │
│    - Agent Loop (strategy → leads → validate → learn) │
└──────────────┬──────────┬────────────┬───────────────┘
               │          │            │
        ┌──────▼──┐ ┌─────▼────┐ ┌────▼─────┐
        │ Neo4j   │ │ Tavily   │ │ Fastino  │
        │ Aura    │ │ Search   │ │ Pioneer  │
        │ (Graph) │ │ (Web)    │ │ (SLM)    │
        └─────────┘ └──────────┘ └──────────┘
```

## Tech Stack

| Layer        | Technology                          | Purpose                                    |
|-------------|-------------------------------------|--------------------------------------------|
| Frontend    | React + TypeScript (Vite)           | Dashboard, graph viz, voice input           |
| Backend     | FastAPI (Python)                    | API, agent loop, background workers         |
| Database    | PostgreSQL (Render)                 | Lead storage, logs                          |
| Graph DB    | Neo4j (Sandbox or Aura free tier)   | Strategy nodes, lessons, relationships      |
| SLM         | Fastino Pioneer (`Qwen/Qwen3-8B`)  | ICP generation, lead scoring, pivots        |
| Web Search  | Tavily API                          | Competitive research, lead fact-checking    |
| Voice       | Modulate API (Velma-2 STT)          | Voice-to-text product description intake    |
| Scout       | Yutori                              | Background monitoring of external signals   |
| Hosting     | Render                              | Web service + static site + Postgres        |

## Neo4j Schema

```cypher
// Strategy nodes (versioned)
(:Strategy {version: INT, icp: STRING, keywords: [STRING], competitors: [STRING], created_at: DATETIME})

// Leads
(:Company {name: STRING, domain: STRING, tech_stack: [STRING], employees: INT, funding: STRING, score: INT})

// Evidence from web research
(:Evidence {source_url: STRING, summary: STRING, retrieved_at: DATETIME})

// Lessons learned from corrections
(:Lesson {lesson_id: STRING, type: STRING, details: STRING, timestamp: DATETIME})
  // types: "TechStackMismatch", "CompanyTooSmall", "ContractLockIn", "SegmentPivot", etc.

// Relationships
(:Strategy)-[:TARGETS]->(:Company)
(:Company)-[:HAS_EVIDENCE]->(:Evidence)
(:Company)-[:LEARNED_FROM]->(:Lesson)
(:Strategy)-[:LEARNED_FROM]->(:Lesson)      // strategy-level pivots
(:Strategy)-[:EVOLVED_FROM]->(:Strategy)

// Constraints
CREATE CONSTRAINT strategy_version IF NOT EXISTS FOR (s:Strategy) REQUIRE s.version IS UNIQUE;
CREATE CONSTRAINT company_domain IF NOT EXISTS FOR (c:Company) REQUIRE c.domain IS UNIQUE;
CREATE CONSTRAINT lesson_id IF NOT EXISTS FOR (l:Lesson) REQUIRE l.lesson_id IS UNIQUE;
CREATE INDEX evidence_url IF NOT EXISTS FOR (e:Evidence) ON (e.source_url);
```

## Key Agent Flows

### Flow 1: Strategy Generation (from product description)
```
Product text → Tavily (competitor research) → Fastino SLM → ICP JSON output
  → Store as Strategy node in Neo4j
  → ICP JSON: { "icp": "...", "keywords": [...], "competitors": [...] }
```

### Flow 2: Lead Validation & Self-Correction
```
For each lead:
  1. Tavily search: "{company} engineering blog tech stack 2026"
  2. Fastino SLM compares CRM data vs. Tavily findings
  3. If mismatch → create Lesson node in Neo4j
  4. Update lead score
  5. If >60% of leads fail validation → trigger Strategy Pivot
```

### Flow 3: Trigger-Based Pivot (Scout)
```
Scout polls target URL every N seconds
  → Status changes to "outage" or "critical"
  → Agent queries lead list for affected companies
  → Drafts context-aware outreach email
  → Logs pivot event to Neo4j
```

## Demo Strategy

### The Mock "Down Event"
Host a simple JSON endpoint (GitHub Gist or separate Render static site):
- **Healthy:** `{"status": "operational", "competitor": "DigitalOcean"}`
- **Outage:** `{"status": "critical_outage", "competitor": "DigitalOcean"}`

During demo, teammate edits the gist/endpoint to trigger the scout live.

### Demo Script (3 minutes)
1. **[0:00–0:30]** Voice-command: "Hunter, find me leads for our new Postgres hosting service."
2. **[0:30–1:00]** Show strategy generation: ICP, keywords, competitors appearing in the UI.
3. **[1:00–1:45]** Show lead list with validation scores. Highlight a self-correction: "Agent found Company X migrated from AWS to GCP — logged a Lesson."
4. **[1:45–2:15]** Trigger the mock outage. Show the scout detecting it and the agent drafting a pivot email in real time.
5. **[2:15–2:45]** Show the Neo4j graph: Strategy evolution, Lesson nodes, Evidence chains.
6. **[2:45–3:00]** Wrap: "No human touched the strategy. The agent learned, pivoted, and improved autonomously."

## Project Structure

```
backend/
├── main.py                          # FastAPI app, routes, middleware
├── setup_neo4j.py                   # Schema setup + synthetic seed data (CLI)
├── requirements.txt
├── .env                             # Local env vars (not committed)
└── services/
    ├── neo4j_service.py             # Neo4j driver, session helper, cleanup
    ├── tavily_service.py            # fact_check_lead(), research_market()
    ├── slm_service.py               # generate_strategy(), score_lead(), refine_strategy(), draft_pivot_email()
    └── modulate_service.py          # transcribe_audio() via Modulate Velma-2 STT

frontend/
├── src/
├── package.json
└── vite.config.ts
```

## Local Development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs on http://localhost:8000

### Neo4j Setup
```bash
cd backend
python setup_neo4j.py              # create constraints + seed data (skip if data exists)
python setup_neo4j.py --reset      # wipe everything, recreate constraints, reseed
python setup_neo4j.py --seed-only  # just insert seed data (no constraint creation)
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173 — API calls are proxied to the backend.

## Environment Variables

```
NEO4J_URI=bolt://<your-sandbox-ip>            # or neo4j+s://<aura-instance>.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<password>
NEO4J_DATABASE=neo4j
TAVILY_API_KEY=<key>
FASTINO_PIONEER_API_KEY=<key>
MODULATE_API_KEY=<key>
YUTORI_API_KEY=<key>
DATABASE_URL=postgresql://<render-postgres-url>
SCOUT_TARGET_URL=<url-to-mock-status-page>
SCOUT_POLL_INTERVAL=10
```

## Deploy to Render

1. Push this repo to GitHub.
2. Go to https://dashboard.render.com → **New** → **Blueprint**.
3. Connect your repo — Render will read `render.yaml`.
4. Set all environment variables in the Render dashboard.
5. Update the `render.yaml` rewrite destination URL with your actual backend service URL.

## Work Split

### Partner A (Backend & Logic — "The Architect")
- Neo4j schema setup and self-correction logic
- Fastino SLM prompts (strategy gen, lead scoring, pivot drafting)
- Tavily fact-check integration
- Agent loop (strategy → leads → validate → learn → repeat)

### Partner B (Infra & UX — "The Orchestrator")
- Render deployment (FastAPI + Postgres live)
- Modulate API voice intake
- Tavily research loop (product desc → competitive landscape)
- Yutori Scout background worker
- React dashboard (activity feed, graph viz, strategy timeline)
- Demo prep (mock trigger, backup recording)
