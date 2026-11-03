from fastapi import FastAPI
from app.routers import junction, address, road

app= FastAPI(title="ASTMA API")
app.include_router(junction.router)
app.include_router(address.router)
app.include_router(road.router)

@app.get("/")
def home():
    return {"message": "ASTMA API is running"}