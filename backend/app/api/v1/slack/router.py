from fastapi import APIRouter
from app.schemas import slack, base
from . import usecases
import logging

router = APIRouter()


@router.post("/", response_model=base.ResBase[slack.ResPush])
def push(
    req: slack.ReqPush,
):
    try:
        result = usecases.push(req)
        return base.ResBase.success(result)
    except Exception as e:
        return base.Error.create("SLACK_PUSH", str(e))

