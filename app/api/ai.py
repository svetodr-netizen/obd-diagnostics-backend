from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.ai_service import analyze_dtc_codes, analyze_single_code, analyze_sensor_anomalies
import json

router = APIRouter(prefix="/ai", tags=["AI"])


class VehicleInfo(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    engine_code: Optional[str] = None


class DTCAnalysisRequest(BaseModel):
    dtc_codes: List[Dict[str, str]]
    vehicle_info: Optional[VehicleInfo] = None
    sensor_data: Optional[Dict[str, Any]] = None


class SingleCodeRequest(BaseModel):
    code: str
    description: str
    vehicle_info: Optional[VehicleInfo] = None


class SensorAnalysisRequest(BaseModel):
    sensor_data: Dict[str, Any]
    vehicle_info: Optional[VehicleInfo] = None


@router.post("/analyze/dtc")
async def analyze_dtc(req: DTCAnalysisRequest):
    vehicle_dict = req.vehicle_info.model_dump() if req.vehicle_info else None

    async def generate():
        async for chunk in analyze_dtc_codes(req.dtc_codes, vehicle_dict, req.sensor_data):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/analyze/code")
async def analyze_code(req: SingleCodeRequest):
    vehicle_dict = req.vehicle_info.model_dump() if req.vehicle_info else None

    async def generate():
        async for chunk in analyze_single_code(req.code, req.description, vehicle_dict):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/analyze/sensors")
async def analyze_sensors(req: SensorAnalysisRequest):
    vehicle_dict = req.vehicle_info.model_dump() if req.vehicle_info else None

    async def generate():
        async for chunk in analyze_sensor_anomalies(req.sensor_data, vehicle_dict):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )