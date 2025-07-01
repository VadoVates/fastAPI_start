import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from http.client import HTTPException
from typing import AsyncGenerator, List

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, DateTime, Float, Integer, Index, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from starlette.responses import StreamingResponse, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DB_PROTOCOL = os.getenv("DB_PROTOCOL")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DB_URL = f"{DB_PROTOCOL}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TemperatureReading(Base):
    __tablename__ = "temperature_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('idx_created_at_desc', desc(created_at)),
    )

class TemperatureData(BaseModel):
    temperature: float
    humidity: float

class TemperatureResponse(BaseModel):
    id: int
    temperature: float
    humidity: float
    created_at: datetime

    class Config:
        from_attributes = True

class StatusResponse(BaseModel):
    status: str
    temperature: float
    humidity: float
    created_at: datetime

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    yield
    logger.info("Application shutting down")

app = FastAPI(lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/data", response_model=StatusResponse)
async def submit_data(data: TemperatureData, db: Session = Depends(get_db)):
    try:
        reading = TemperatureReading(temperature=data.temperature, humidity=data.humidity)
        db.add(reading)
        db.commit()
        db.refresh(reading)

        logger.info(
            f"Received data: Temp={reading.temperature}°C, Humidity={reading.humidity}%, "
            f"Created_at: {reading.created_at}"
        )

        return StatusResponse(
            status="success",
            temperature=reading.temperature,
            humidity=reading.humidity,
            created_at=reading.created_at,
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")

@app.get("/history", response_model=List[TemperatureResponse])
async def history(limit: int = 96, db: Session = Depends(get_db)):
    try:
        readings = (
            db.query(TemperatureReading)
            .order_by(TemperatureReading.created_at.desc())
            .limit(limit)
            .all()
        )
        return readings
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

@app.get("/stream")
async def stream():
    async def event_generator() -> AsyncGenerator[str, None]:
        last_id = None

        while True:
            db = SessionLocal()
            try:
                latest = (
                    db.query(TemperatureReading)
                    .order_by(TemperatureReading.created_at.desc())
                    .first()
                )
                if latest and latest.id != last_id:
                    last_id = latest.id
                    event_data = {
                        "id": latest.id,
                        "temperature": latest.temperature,
                        "humidity": latest.humidity,
                        "created_at": latest.created_at.isoformat()
                    }
                    yield f"data: {event_data}\n\n"
                else:
                    yield ": keepalive\n\n"
            except SQLAlchemyError as e:
                logger.error(f"Database error in stream: {e}")
                yield f"event: error\ndata: Database connection error\n\n"
            finally:
                db.close()

            await asyncio.sleep(30)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        },
    )

@app.head("/")
async def head():
    return Response(status_code=200)

@app.get("/")
async def root():
    return {
        "message": "I'm alive!",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database connection error occurred")