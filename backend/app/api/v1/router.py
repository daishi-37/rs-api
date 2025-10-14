from fastapi import APIRouter
from .slack.router import router as slack_router


router = APIRouter()

router.include_router(slack_router, prefix="/slack", tags=["v1_Slack"])
