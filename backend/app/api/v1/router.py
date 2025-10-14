from fastapi import APIRouter
from .slack.router import router as slack_router
from .media.router import router as media_router


router = APIRouter()

router.include_router(slack_router, prefix="/slack", tags=["v1_Slack"])
router.include_router(media_router, prefix="/media", tags=["v1_Media"])
