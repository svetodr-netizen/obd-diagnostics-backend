from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import ws_manager
import logging

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    from app.services.obd_service import obd_service
    await ws_manager.send_personal(websocket, {
        "type": "connection",
        "obd_connected": obd_service.is_connected,
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await ws_manager.send_personal(websocket, {"type": "pong"})

            elif msg_type == "read_sensors":
                if obd_service.is_connected:
                    sensors = await obd_service.read_all_sensors()
                    await ws_manager.send_personal(websocket, {
                        "type": "sensor_update",
                        "data": sensors,
                    })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS error: {e}")
        ws_manager.disconnect(websocket)