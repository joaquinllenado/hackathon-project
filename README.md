# Hackathon App

Fullstack app: **FastAPI** backend + **React + TypeScript** frontend (Vite).

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs on http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on http://localhost:5173 — API calls are proxied to the backend.

## Deploy to Render

1. Push this repo to GitHub.
2. Go to https://dashboard.render.com → **New** → **Blueprint**.
3. Connect your repo — Render will read `render.yaml`.
4. Update the `render.yaml` rewrite destination URL with your actual backend service URL once deployed.
