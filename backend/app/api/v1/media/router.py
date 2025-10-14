from fastapi import APIRouter
from app.schemas import slack, base
from backend.app.usecases.media import splitSize as usecases
import logging

router = APIRouter()


@router.post("/split-by-size", response_model=base.ResBase[slack.ResPush])
def splitSize(
    req: slack.ReqPush,
):
    try:
        result = usecases.split(req)
        return base.ResBase.success(result)
    except Exception as e:
        return base.Error.create("SLACK_PUSH", str(e))

