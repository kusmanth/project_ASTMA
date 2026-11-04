from fastapi import FastAPI
from app.routers import junction, address, road, signal

app= FastAPI(title="ASTMA API")
app.include_router(junction.router)
app.include_router(address.router)
app.include_router(road.router)
app.include_router(signal.router)


@app.get("/")
def home():
    return {"message": "ASTMA API is running"}