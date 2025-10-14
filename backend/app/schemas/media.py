from typing import List
from pydantic import BaseModel, Field
from app.schemas import base


class ResBase(BaseModel):
    media_urls: List[str] = Field(..., example=[], description="分割されたメディアのURLリスト")

class ResSplit(ResBase):
    pass