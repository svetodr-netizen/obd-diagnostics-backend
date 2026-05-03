import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._streaming = False
        self._stream_task: asyncio.Task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, data: dict):
        if not self.active_connections:
            return
        message = json.dumps(data)
        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self.active_connections -= dead

    async def send_personal(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Send failed: {e}")

    async def start_live_stream(self, interval_ms: int = 500):
        from app.services.obd_service import obd_service
        if self._streaming:
            return
        self._streaming = True
        async def _stream():
            while self._streaming:
                if not obd_service.is_connected:
                    await self.broadcast({"type": "error", "message": "OBD nije spojen"})
                    break
                sensors = await obd_service.read_all_sensors()
                await self.broadcast({"type": "sensor_update", "data": sensors})
                await asyncio.sleep(interval_ms / 1000)
        self._stream_task = asyncio.create_task(_stream())

    async def stop_live_stream(self):
        self._streaming = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None


ws_manager = ConnectionManager()