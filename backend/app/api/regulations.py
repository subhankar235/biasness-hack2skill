# app/api/regulations.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Dataset, Remediation
from app.dependencies import get_db

router = APIRouter()


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class RemediationRequest(BaseModel):
    dataset_id: str
    sensitive_col: str
    target_col: str
    strategy: str


class RemediationResponse(BaseModel):
    remediation_id: str
    status: str
    strategy: str


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("/run", response_model=RemediationResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_remediation(
    req: RemediationRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).where(Dataset.id == req.dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    remediation_id = str(uuid.uuid4())
    record = Remediation(
        id=remediation_id,
        bias_run_id=str(uuid.uuid4()),
        strategy=req.strategy,
    )
    db.add(record)
    await db.commit()

    return RemediationResponse(remediation_id=remediation_id, status="pending", strategy=req.strategy)