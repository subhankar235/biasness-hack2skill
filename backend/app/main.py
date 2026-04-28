from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    datasets,
    bias,
    reports,
    models,
    remediation,
)

app = FastAPI(title="FairLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FairLens API running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

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
    models.router,
    prefix="/api/v1/models",
    tags=["Models"]
)

app.include_router(
    reports.router,
    prefix="/api/v1/report",
    tags=["Reports"]
)

app.include_router(
    remediation.router,
    prefix="/api/v1/remediation",
    tags=["Remediation"]
)