from fastapi import APIRouter, UploadFile, File
import pandas as pd
from io import BytesIO

from app.core.shap_engine import run_shap_analysis

router = APIRouter()

@router.post("/explain")
async def explain_model(file: UploadFile = File(...)):
    contents = await file.read()

    df = pd.read_csv(BytesIO(contents))

    result = run_shap_analysis(df)

    return result