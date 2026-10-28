import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.config import get_settings
from app.routes import signups

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.load()
    yield


app = FastAPI(title="Proof of Demand backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().web_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(signups.router)


@app.get("/health")
def health():
    return {"ok": True, "models_loaded": models.loaded}
