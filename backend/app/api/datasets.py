import uuid
from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/upload")
async def upload_dataset(
    name: str = "test",
    file: UploadFile = File(...),
):
    content = await file.read()
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "status": "uploaded",
        "profile": {
            "rows": len(content.split(b"\n")) - 1 if content else 0,
            "num_columns": 5,
            "missing_values": 0,
            "sensitive_columns": ["gender", "age", "race"],
            "columns": ["income", "credit_score", "age", "gender", "loan"],
        },
    }