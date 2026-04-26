# app/api/remediation.py
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Dataset, Remediation, User
from app.dependencies import get_current_user, get_db
from app.storage.s3 import download_parquet
from app.tasks.remediation_tasks import run_remediation_task

router = APIRouter()


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class RemediationRequest(BaseModel):
    dataset_id: str
    sensitive_col: str
    target_col: str
    strategy: Literal["reweight", "resample", "threshold"]


class RemediationResponse(BaseModel):
    remediation_id: str
    status: str          # pending | running | done | error
    strategy: str
    method_description: str | None = None
    before: dict | None = None
    after: dict | None = None
    improvement_pct: float | None = None
    verdict: str | None = None
    group_thresholds: dict | None = None   # only for threshold strategy


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("/run", response_model=RemediationResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_remediation(
    req: RemediationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kick off a remediation job (async via Celery).
    Returns immediately with status=pending and a remediation_id to poll.
    """
    # Verify dataset belongs to user's org
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == req.dataset_id,
            Dataset.org_id == current_user.org_id,
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    remediation_id = str(uuid.uuid4())

    # Persist pending record
    record = Remediation(
        id=remediation_id,
        bias_run_id=None,          # not linked to a BiasRun in this flow
        strategy=req.strategy,
        params={
            "dataset_id": req.dataset_id,
            "sensitive_col": req.sensitive_col,
            "target_col": req.target_col,
        },
        before_metrics=None,
        after_metrics=None,
    )
    db.add(record)
    await db.flush()

    # Dispatch Celery task
    run_remediation_task.delay(
        remediation_id=remediation_id,
        s3_key=dataset.s3_key,
        sensitive_col=req.sensitive_col,
        target_col=req.target_col,
        strategy=req.strategy,
    )

    return RemediationResponse(
        remediation_id=remediation_id,
        status="pending",
        strategy=req.strategy,
    )


@router.get("/{remediation_id}", response_model=RemediationResponse)
async def get_remediation(
    remediation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll for job result."""
    result = await db.execute(
        select(Remediation).where(Remediation.id == remediation_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Remediation job not found")

    # Determine status from DB fields
    if record.before_metrics and record.after_metrics:
        job_status = "done"
    elif record.before_metrics is None and record.after_metrics is None:
        job_status = "pending"
    else:
        job_status = "running"

    after = record.after_metrics or {}

    return RemediationResponse(
        remediation_id=remediation_id,
        status=job_status,
        strategy=record.strategy,
        method_description=after.get("method_description"),
        before=record.before_metrics,
        after={k: v for k, v in after.items() if k != "method_description"} if after else None,
        improvement_pct=after.get("improvement_pct"),
        verdict=after.get("verdict"),
        group_thresholds=after.get("group_thresholds"),
    )


@router.get("/history/all")
async def list_remediations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all remediation runs for the current user's org (most recent first)."""
    result = await db.execute(
        select(Remediation).order_by(Remediation.id.desc()).limit(50)
    )
    records = result.scalars().all()
    return [
        {
            "remediation_id": r.id,
            "strategy": r.strategy,
            "params": r.params,
            "status": "done" if (r.before_metrics and r.after_metrics) else "pending",
            "improvement_pct": (r.after_metrics or {}).get("improvement_pct"),
            "verdict": (r.after_metrics or {}).get("verdict"),
        }
        for r in records
    ]