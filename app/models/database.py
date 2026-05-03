from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
from app.core.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True)
    vin = Column(String(17), unique=True, nullable=True)
    make = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    engine_code = Column(String(20))
    protocol = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("DiagnosticSession", back_populates="vehicle")


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    dtc_codes = Column(JSON, default=list)
    ai_analysis = Column(Text, nullable=True)
    sensor_snapshot = Column(JSON, nullable=True)
    vehicle = relationship("Vehicle", back_populates="sessions")
    dtc_records = relationship("DTCRecord", back_populates="session")


class DTCRecord(Base):
    __tablename__ = "dtc_records"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("diagnostic_sessions.id"))
    code = Column(String(10))
    description = Column(Text)
    status = Column(String(20))
    ai_explanation = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session = relationship("DiagnosticSession", back_populates="dtc_records")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        yield session