from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.database import get_session, DiagnosticSession
from app.services.pdf_service import generate_pdf_report
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/sessions")
async def get_sessions(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(DiagnosticSession).order_by(desc(DiagnosticSession.started_at)).limit(50)
    )
    sessions = result.scalars().all()
    return {"sessions": [
        {
            "id": s.id,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "dtc_codes": s.dtc_codes,
            "ai_analysis": s.ai_analysis,
            "sensor_snapshot": s.sensor_snapshot,
        }
        for s in sessions
    ]}


class SaveSessionRequest(BaseModel):
    dtc_codes: List[Dict]
    ai_analysis: Optional[str] = None
    sensor_snapshot: Optional[Dict] = None
    vehicle_info: Optional[Dict] = None


@router.post("/sessions")
async def save_session(req: SaveSessionRequest, db: AsyncSession = Depends(get_session)):
    session = DiagnosticSession(
        started_at=datetime.utcnow(),
        dtc_codes=req.dtc_codes,
        ai_analysis=req.ai_analysis,
        sensor_snapshot=req.sensor_snapshot,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": session.id, "success": True}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(DiagnosticSession).where(DiagnosticSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
    return {"success": True}


@router.get("/sessions/{session_id}/pdf")
async def export_pdf(session_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(DiagnosticSession).where(DiagnosticSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return Response(status_code=404)
    
    pdf_bytes = generate_pdf_report(
        dtc_codes=session.dtc_codes or [],
        ai_analysis=session.ai_analysis or "",
        sensor_data=session.sensor_snapshot,
        vehicle_info=None,
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=dijagnostika_{session_id}.pdf"}
    )