from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.modulate_service import transcribe_audio
from agent.strategy import run_strategy_generation

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductInput(BaseModel):
    description: str


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