# TODO — The Recursive Hunter

## Phase 1: Foundation (11:00–11:45)

### Partner A (Backend & Logic)
- [ ] Create 30–50 mock sales scenario JSON examples for Fastino Pioneer fine-tuning
  - Input: product description → Output: ICP JSON (`{ "icp", "keywords", "competitors" }`)
  - Input: lead + evidence → Output: validation score + reasoning
- [ ] Upload dataset and kick off Fastino Pioneer training run
- [ ] Set up Neo4j Aura free instance — get connection URI, user, password

### Partner B (Infra & UX)
- [ ] Deploy the FastAPI scaffold to Render (web service live with `/api/hello`)
- [ ] Provision Render Postgres — get `DATABASE_URL`
- [ ] Add all env vars to Render dashboard (Neo4j, Tavily, Fastino, Modulate, DB, Scout)
- [ ] Create the mock status page (GitHub Gist or Render static site)
  - Content: `{"status": "operational", "competitor": "DigitalOcean"}`

---

## Phase 2: Integration (11:45–1:00)

### Partner A
- [ ] Define Neo4j schema in a setup script (`backend/setup_neo4j.py`)
  - Nodes: `Strategy`, `Company`, `Evidence`, `Lesson`
  - Relationships: `TARGETS`, `HAS_EVIDENCE`, `LEARNED_FROM`, `EVOLVED_FROM`
  - Include sample seed data for testing
- [ ] Write Tavily fact-check function (`backend/services/tavily_service.py`)
  - `async def fact_check_lead(company_name, claimed_tech_stack) -> dict`
  - Returns: `{ "actual_tech": [...], "sources": [...], "mismatch": bool }`
- [ ] Write Tavily competitor research function
  - `async def research_market(product_description) -> dict`
  - Returns: `{ "competitors": [...], "pricing_insights": [...], "complaints": [...] }`

### Partner B
- [ ] Integrate Modulate API for voice-to-text (`backend/services/modulate_service.py`)
- [ ] Connect Tavily client in backend (`pip install tavily-python`, add to requirements)
- [ ] Build `POST /api/product` endpoint — accepts product description text, stores it, kicks off agent
- [ ] Set up WebSocket `/api/ws/feed` for real-time agent activity streaming to frontend

---

## Phase 3: The Agent Loop (1:30–3:30)

### Partner A
- [ ] Download fine-tuned Fastino model / configure API client (`backend/services/slm_service.py`)
- [ ] Implement strategy generation flow:
  1. Receive product description
  2. Call Tavily `research_market()`
  3. Feed product + market data to Fastino SLM
  4. Parse ICP JSON output
  5. Store `Strategy` node in Neo4j
- [ ] Implement lead validation loop:
  1. For each lead, call `fact_check_lead()`
  2. Compare CRM data vs Tavily results via SLM
  3. Score the lead (0–100)
  4. If mismatch → create `Lesson` node, link to `Company`
  5. If >60% leads fail → trigger strategy pivot
- [ ] Implement self-correction logic:
  - Before generating new strategy, query Neo4j for all `Lesson` nodes
  - Inject lessons into SLM prompt as context
  - Create new `Strategy` node with `EVOLVED_FROM` edge to previous
- [ ] Implement pivot email drafting (SLM prompt for outage-context outreach)

### Partner B
- [ ] Implement Yutori Scout background worker (`backend/workers/scout.py`)
  - Polls `SCOUT_TARGET_URL` every `SCOUT_POLL_INTERVAL` seconds
  - On status change → push event to agent loop + WebSocket feed
- [ ] Build `POST /api/mock-trigger` endpoint (manual trigger for demo)
- [ ] Build `GET /api/strategy` endpoint — returns current strategy from Neo4j
- [ ] Build `GET /api/leads` endpoint — returns scored leads
- [ ] Build `GET /api/lessons` endpoint — returns lesson log
- [ ] Build `GET /api/graph` endpoint — returns Neo4j subgraph as JSON for frontend viz
- [ ] Build React dashboard:
  - [ ] Product description input (text box + mic button for Modulate)
  - [ ] Real-time agent activity feed (WebSocket)
  - [ ] Lead table with validation scores
  - [ ] Strategy panel showing current ICP, keywords, competitors
  - [ ] Neo4j graph visualization (use a lib like `react-force-graph` or `vis-network`)
  - [ ] Strategy evolution timeline

---

## Phase 4: Polish & Demo (3:30–4:15)

### Partner A
- [ ] End-to-end test: product description → strategy → leads → validation → lesson → improved strategy
- [ ] Verify Neo4j graph looks good for demo (clear nodes, readable labels)
- [ ] Script the exact demo inputs (product description, timing of mock trigger)

### Partner B
- [ ] Final UI polish — make sure graph viz and activity feed look clean
- [ ] Test mock trigger flow: edit gist → scout detects → agent reacts → UI updates
- [ ] Record backup video of the full demo flow (screen capture)
- [ ] Prepare 3-minute pitch script

---

## Phase 5: Submit (4:15–4:30)
- [ ] Verify Render URLs are live and functional
- [ ] Double-check all env vars are set on Render
- [ ] Submit to judges
- [ ] Have backup video ready in case of live demo issues

---

## Quick Reference: API Keys Needed
- [ ] Neo4j Aura — https://neo4j.com/cloud/aura-free/
- [ ] Tavily — https://tavily.com/
- [ ] Fastino Pioneer — (hackathon sponsor)
- [ ] Modulate — (hackathon sponsor)
- [ ] Yutori — (hackathon sponsor)
