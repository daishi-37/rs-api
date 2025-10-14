from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas import base


class ResBase(BaseModel):
    msg: str = Field(..., example="slack message")


class ReqBase(BaseModel):
    msg: str = Field(..., example="slack push successfully")


class ResPush(ResBase):
    pass


class ReqPush(ReqBase):
    pass