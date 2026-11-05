
from fastapi import FastAPI
from app.routers import (
    junction,
    address,
    road,
    signal,
    traffic_reading,
    signal_timing,
)

app = FastAPI(title="ASTMA API")

app.include_router(junction.router)
app.include_router(address.router)
app.include_router(road.router)
app.include_router(signal.router)
app.include_router(traffic_reading.router)
app.include_router(signal_timing.router)


@app.get("/")
def home():
    return {"message": "ASTMA API is running"}

