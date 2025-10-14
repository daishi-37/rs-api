import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from app.core.exception import add_exception_handlers
from app.core import settings
from app.api.v1.router import router
from app.usecases.media import clean_files

# スケジューラの作成
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    clean_files()
    
    scheduler.add_job(clean_files, 'interval', hours=12)
    scheduler.start()
    
    yield
    
    scheduler.shutdown()


app = FastAPI(
    root_path=settings.BASE_PATH,
    title="RS Api",
    description="",
    version="0.1.0",
    docs_url=f"{settings.API_PATH}/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=f"{settings.API_PATH}/v1")

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

add_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
