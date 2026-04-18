from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import datasets, bias, models, narratives, regulations, remediation, monitoring, reports, orgs, auth, benchmark

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

app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])
app.include_router(bias.router, prefix="/api/v1/bias", tags=["Bias"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(narratives.router, prefix="/api/v1/narratives", tags=["Narratives"])
app.include_router(regulations.router, prefix="/api/v1/regulations", tags=["Regulations"])
app.include_router(remediation.router, prefix="/api/v1/remediation", tags=["Remediation"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(orgs.router, prefix="/api/v1/orgs", tags=["Organizations"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(benchmark.router, prefix="/api/v1/benchmark", tags=["Benchmark"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.on_event("startup")
async def startup_event():
    pass

@app.on_event("shutdown")
async def shutdown_event():
    pass