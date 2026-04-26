from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import datasets, bias, reports

app = FastAPI(
    title="FairLens API",
    description="AI Fairness and Bias Detection Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    datasets.router,
    prefix="/api/v1/datasets",
    tags=["Datasets"]
)

app.include_router(
    bias.router,
    prefix="/api/v1/bias",
    tags=["Bias"]
)

app.include_router(
    reports.router, 
    prefix="/api/v1/report", 
    tags=["Report"]
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "FairLens API"
    }

@app.on_event("startup")
async def startup_event():
    print("FairLens API started")

@app.on_event("shutdown")
async def shutdown_event():
    print("FairLens API stopped")