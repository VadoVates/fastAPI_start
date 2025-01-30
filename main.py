from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TemperatureData(BaseModel):
    temperature: float
    humidity: float

@app.post("/data")
async def temperature(data: TemperatureData):
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Received data: Temp={data.temperature}°C, Humidity={data.humidity}%")
    return {
        "status": "ok",
        "data": data.temperature,
        "humidity": data.humidity
    }


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
