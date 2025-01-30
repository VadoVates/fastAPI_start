import asyncio
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, DateTime, Float, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from starlette.responses import StreamingResponse

app = FastAPI()

load_dotenv()
DATABASE_URL = (os.getenv("DB_PROTOCOL") + '://' + os.getenv("DB_USER") + ':' + os.getenv("DB_PASSWORD") + '@'
                + os.getenv("DB_HOST") + ':' + os.getenv("DB_PORT") + '/' + os.getenv("DB_NAME") + '?sslmode=require')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TemperatureReading(Base):
    # noinspection SpellCheckingInspection
    __tablename__ = "temperature_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TemperatureData(BaseModel):
    temperature: float
    humidity: float

@app.post("/data")
async def temperature(data: TemperatureData, db: Session = Depends(get_db)):
    reading = TemperatureReading(temperature=data.temperature, humidity=data.humidity)
    db.add(reading)
    db.commit()
    db.refresh(reading)

    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Received data: Temp={data.temperature}°C, Humidity={data.humidity}%")
    return {
        "status": "ok",
        "data": reading.temperature,
        "humidity": reading.humidity,
        "timestamp": reading.timestamp,
    }

@app.get("/history")
async def history(db: Session = Depends(get_db)):
    readings = db.query(TemperatureReading).order_by(TemperatureReading.timestamp.desc()).limit(10).all()
    return [
        {
            "id" : r.id,
            "temperature" : r.temperature,
            "humidity" : r.humidity,
            "timestamp" : r.timestamp
        }
        for r in readings
    ]

@app.get("/stream")
async def stream(db: Session = Depends(get_db)):
    async def event_generator() -> AsyncGenerator[str, None]:
        last_id = None

        while True:
            latest = db.query(TemperatureReading).order_by(TemperatureReading.timestamp.desc()).first()
            if latest and latest.id != last_id:
                last_id = latest.id

                yield f"data: {latest.temperature},{latest.humidity},{latest.timestamp}\n\n"

            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
async def root():
    return {"message": "I'm alive!" }