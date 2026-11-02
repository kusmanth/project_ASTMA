from fastapi import FastAPI
from app.routers import junction, address

app= FastAPI(title="ASTMA API")
app.include_router(junction.router)
app.include_router(address.router)

@app.get("/")
def home():
    return {"message": "ASTMA API is running"}