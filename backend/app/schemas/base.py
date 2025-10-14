from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar


T = TypeVar('T')


class Error(BaseModel):
    code: str
    msg: str

    @classmethod
    def create(cls, operation: str, msg: str):
        code = f"{operation.upper()}_ERROR"
        return cls(code=code, msg=msg)


class ResBase(BaseModel, Generic[T]):
    is_success: Optional[bool] = None
    data: Optional[T] = None
    errors: Optional[List[Error]] = None

    @classmethod
    def success(cls, data: T = None):
        return cls(
            is_success=True,
            data=data if data is not None else {},
            errors=[]
        )

    @classmethod
    def warning(cls, data: T = None, errors: List[Error] = None):
        return cls(
            is_success=True,
            data=data if data is not None else {},
            errors=errors if errors is not None else []
        )

    @classmethod
    def error(cls, errors: List[Error], status_code: int = 400):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status_code,
            detail=cls(is_success=False, data={}, errors=errors).dict()
        )


class ReqBasePagination(BaseModel):
    page: int = Field(1, example=1)
    per_page: int = Field(10, example=100)


class ResBasePagination(BaseModel, Generic[T]):
    items: List[T] = Field(...)
    total: int = Field(..., example=0)
    page: int = Field(..., example=1)
    per_page: int = Field(..., example=10)
    total_pages: int = Field(..., example=1)
    has_next: bool = Field(..., example=False)
    has_prev: bool = Field(..., example=False)

    @classmethod
    def calc_pagination(
        cls,
        items: List[T],
        total: int,
        page: int,
        per_page: int
    ):
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1

        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
