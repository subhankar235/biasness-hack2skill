import uuid
from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    return {"model_id": str(uuid.uuid4()), "status": "uploaded"}


@router.post("/explain")
def explain_model(model_id: str, dataset_id: str):
    return {"shap_values": [0.1, 0.2, 0.15]}