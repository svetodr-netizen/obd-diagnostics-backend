from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.models.database import init_db
from app.api import obd, ai, ws, history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pokretanje OBD-AI Diagnostics...")
    await init_db()
    yield
    logger.info("Gašenje...")
    from app.services.obd_service import obd_service
    from app.services.ws_manager import ws_manager
    await ws_manager.stop_live_stream()
    await obd_service.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(obd.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(ws.router)
app.include_router(history.router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}