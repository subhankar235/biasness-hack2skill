from fastapi import APIRouter, UploadFile, File
import pandas as pd
from io import StringIO
from app.core.profiler import profile_dataframe
from app.api.bias import set_dataframe

router = APIRouter()

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_csv(StringIO(content.decode("utf-8")))

    set_dataframe(df)

    result = profile_dataframe(df)

    return result