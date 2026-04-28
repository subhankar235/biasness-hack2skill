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
        "row_count": len(content),
        "status": "uploaded",
    }