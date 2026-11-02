from fastapi import FastAPI
from app.routers import junction

app= FastAPI(title="ASTMA API")
app.include_router(junction.router)

@app.get("/")
def home():
    return {"message": "ASTMA API is running"}