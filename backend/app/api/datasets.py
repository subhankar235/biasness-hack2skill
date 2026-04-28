import uuid
import pandas as pd
from io import BytesIO

from fastapi import APIRouter, UploadFile, File

router = APIRouter()


def detect_sensitive_columns(columns):
    keywords = [
        "gender",
        "sex",
        "race",
        "religion",
        "age",
        "ethnicity",
        "marital",
    ]

    found = []

    for col in columns:
        name = col.lower()

        if any(word in name for word in keywords):
            found.append(col)

    return found


@router.post("/upload")
async def upload_dataset(
    name: str = "test",
    org_id: str = "test",
    file: UploadFile = File(...),
):
    content = await file.read()

    # CSV read
    df = pd.read_csv(BytesIO(content))

    profile = {
        "rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "missing_values": int(df.isnull().sum().sum()),
        "columns": list(df.columns),
        "sensitive_columns": detect_sensitive_columns(df.columns),
    }

    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "org_id": org_id,
        "status": "uploaded",
        "profile": profile,
    }