from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.base import ResBase, Error
from app.core.logger import main_logger, hc_err_logger


def http_exception_handler(request: Request, exc: HTTPException):
    main_logger.warning(f"HTTP例外が発生しました: {request.method} {request.url} - {exc.status_code}: {exc.detail}")
    hc_err_logger.warning(f"HTTP exception occured: {request.method} {request.url} - {exc.status_code}: {exc.detail}")

    # exc.detailが既にResBase形式の辞書の場合はそのまま返す
    if isinstance(exc.detail, dict) and "is_success" in exc.detail and "data" in exc.detail and "errors" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    # それ以外の場合は従来通りの処理
    error = Error.create("HTTP", str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=ResBase(is_success=False, data={}, errors=[error]).dict()
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    main_logger.warning(f"バリデーション例外が発生しました: {request.method} {request.url} - {exc.errors()}")
    hc_err_logger.warning(f"Validation exception occured: {request.method} {request.url} - {exc.errors()}")
    errors = []
    for error in exc.errors():
        error_msg = f"{' -> '.join(str(loc) for loc in error['loc'])}: {error['msg']}"
        errors.append(Error.create("VALIDATION", error_msg))

    return JSONResponse(
        status_code=422,
        content=ResBase(is_success=False, data={}, errors=errors).dict()
    )


def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    error_msg = str(exc)
    traceback_str = traceback.format_exc()

    main_logger.error(f"予期しない例外が発生しました: {request.method} {request.url}")
    main_logger.error(f"例外の詳細: {error_msg}")
    main_logger.error(f"トレースバック:\n{traceback_str}")
    hc_err_logger.error(f"Unexpected exception occured: {request.method} {request.url} - {error_msg} - {traceback_str}")

    error = Error.create("INTERNAL", "An unexpected error occurred.")
    return JSONResponse(
        status_code=500,
        content=ResBase(is_success=False, data={}, errors=[error]).dict()
    )


def add_exception_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
