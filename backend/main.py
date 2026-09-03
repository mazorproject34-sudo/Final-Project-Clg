"""
FastAPI Server Entrypoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import hazards, alerts, evacuation, shelters

app = FastAPI(
    title="Intelligent Multi-Hazard Disaster Decision-Support Platform API",
    version="1.0.0"
)

# Enable CORS for local React + Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(hazards.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(evacuation.router, prefix="/api/v1")
app.include_router(shelters.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "status": "online",
        "platform": "Intelligent Multi-Hazard Disaster Decision-Support Platform",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
