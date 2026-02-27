from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from services.modulate_service import transcribe_audio
from services.feed_manager import feed_manager
from agent.strategy import run_strategy_generation
from agent.validation import run_validation_loop
from agent.pivot import run_pivot_drafting

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MAX_DESCRIPTION_LENGTH = 10_000


class ProductInput(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("description must not be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_max_length(cls, v: str) -> str:
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"description must not exceed {MAX_DESCRIPTION_LENGTH} characters")
        return v


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!"}


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    result = await transcribe_audio(file)
    return result


@app.post("/api/product")
async def ingest_product(payload: ProductInput):
    result = await run_strategy_generation(payload.description)
    return result


@app.post("/api/validate")
async def validate_leads(strategy_version: int | None = None):
    result = await run_validation_loop(strategy_version)
    return result


class TriggerInput(BaseModel):
    status: str = "critical_outage"
    competitor: str = "DigitalOcean"


@app.post("/api/mock-trigger")
async def mock_trigger(payload: TriggerInput):
    result = await run_pivot_drafting(payload.model_dump())
    return result

@app.websocket("/api/ws/feed")
async def ws_feed(websocket: WebSocket):
    await feed_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        feed_manager.disconnect(websocket)
