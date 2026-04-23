from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
from app.core.metrics import demographic_parity

router = APIRouter()

TEMP_DF = None

def set_dataframe(df):
    global TEMP_DF
    TEMP_DF = df

class ScanRequest(BaseModel):
    target_column: str
    sensitive_column: str
    positive_value: int = 1

@router.post("/set-temp")
def set_temp_data(data: dict):
    global TEMP_DF
    TEMP_DF = pd.DataFrame(data["rows"])
    return {"status": "loaded"}

@router.post("/scan")
def run_scan(req: ScanRequest):
    global TEMP_DF

    if TEMP_DF is None:
        return {"error": "No dataset loaded"}

    return demographic_parity(
        TEMP_DF,
        req.sensitive_column,
        req.target_column,
        req.positive_value
    )