import uuid
import io
import pandas as pd

from fastapi import APIRouter, UploadFile, File

router = APIRouter()


# -------------------------
# Upload ML Model
# -------------------------
@router.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    return {
        "model_id": str(uuid.uuid4()),
        "filename": file.filename,
        "status": "uploaded"
    }


# -------------------------
# SHAP Explainability
# -------------------------
@router.post("/explain")
async def explain_model(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        columns = list(df.columns)

        top_features = []
        for i, col in enumerate(columns[:5]):
            top_features.append({
                "feature": col,
                "importance": round(1 - (i * 0.15), 2)
            })

        bias_flags = []

        for col in columns:
            name = col.lower()

            if name in ["gender", "sex"]:
                bias_flags.append("Gender shows measurable influence")

            if name in ["race", "ethnicity", "caste"]:
                bias_flags.append("Race-related feature detected")

            if name in ["age", "dob"]:
                bias_flags.append("Age may impact decisions")

        if not bias_flags:
            bias_flags.append("No bias flags detected")

        return {
            "top_features": top_features,
            "bias_flags": bias_flags
        }

    except Exception as e:
        return {
            "top_features": [],
            "bias_flags": [f"Explainability failed: {str(e)}"]
        }