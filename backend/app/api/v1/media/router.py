from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from app.schemas import base, media
from app.usecases import media as usecases

router = APIRouter()


@router.post("/split-by-size", response_model=base.ResBase[media.ResBase])
def split_by_size(
    file: UploadFile = File(...),
    size: int = Form(..., description="分割するファイル容量(MB)"),
):
    try:
        result = usecases.split_by_size(file, size)
        return base.ResBase.success(result)
    except Exception as e:
        return base.Error.create("MEDIA_SPLIT_BY_SIZE", str(e))
