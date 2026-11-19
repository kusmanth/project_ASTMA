
from fastapi import FastAPI
from app.routers import (
    agent,
    junction,
    address,
    road,
    signal,
    traffic_reading,
    signal_timing,user,
    emergency_trip,
    route_request,emergency_vehicle,hospital,police_station
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ASTMA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(junction.router)
app.include_router(address.router)
app.include_router(road.router)
app.include_router(signal.router)
app.include_router(traffic_reading.router)
app.include_router(signal_timing.router)
app.include_router(user.router)
app.include_router(emergency_vehicle.router)
app.include_router(emergency_trip.router)
app.include_router(route_request.router)
app.include_router(hospital.router)
app.include_router(police_station.router)
app.include_router(agent.router)

@app.get("/")
def home():
    return {"message": "ASTMA API is running"}

