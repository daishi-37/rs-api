from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exception import add_exception_handlers
from app.core import settings
from app.api.v1.router import router


app = FastAPI(
    root_path=settings.BASE_PATH,
    title="RS Api",
    description="",
    version="0.1.0",
    docs_url=f"{settings.API_PATH}/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=f"{settings.API_PATH}/v1")

add_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )