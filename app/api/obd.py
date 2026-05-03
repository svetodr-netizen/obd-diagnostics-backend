from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.obd_service import obd_service
from app.services.ws_manager import ws_manager

router = APIRouter(prefix="/obd", tags=["OBD"])


class ConnectRequest(BaseModel):
    port: Optional[str] = None


class StreamRequest(BaseModel):
    interval_ms: int = 500


@router.get("/ports")
async def list_ports():
    return {"ports": obd_service.list_ports()}


@router.post("/connect")
async def connect(req: ConnectRequest):
    result = await obd_service.connect(req.port)
    if not result["success"]:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@router.post("/disconnect")
async def disconnect():
    await ws_manager.stop_live_stream()
    await obd_service.disconnect()
    return {"success": True}


@router.get("/status")
async def status():
    return {
        "connected": obd_service.is_connected,
        "streaming": ws_manager._streaming,
    }


@router.get("/dtc")
async def get_dtc():
    if not obd_service.is_connected:
        raise HTTPException(status_code=503, detail="OBD nije spojen")
    codes = await obd_service.get_dtc_codes()
    return {"codes": [{"code": c.code, "description": c.description} for c in codes]}


@router.delete("/dtc")
async def clear_dtc():
    if not obd_service.is_connected:
        raise HTTPException(status_code=503, detail="OBD nije spojen")
    success = await obd_service.clear_dtc_codes()
    return {"success": success}


@router.get("/sensors")
async def get_sensors():
    if not obd_service.is_connected:
        raise HTTPException(status_code=503, detail="OBD nije spojen")
    sensors = await obd_service.read_all_sensors()
    return {"sensors": sensors}


@router.get("/vin")
async def get_vin():
    if not obd_service.is_connected:
        raise HTTPException(status_code=503, detail="OBD nije spojen")
    vin = await obd_service.get_vin()
    return {"vin": vin}


@router.post("/stream/start")
async def start_stream(req: StreamRequest):
    if not obd_service.is_connected:
        raise HTTPException(status_code=503, detail="OBD nije spojen")
    await ws_manager.start_live_stream(req.interval_ms)
    return {"success": True}


@router.post("/stream/stop")
async def stop_stream():
    await ws_manager.stop_live_stream()
    return {"success": True}