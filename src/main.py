from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from src.db.database import engine
from src.models import Base
from src.auth import routes as auth_routes
from src.domain.expense import routes as expense_routes
from src.config import settings
from src.errors.main import AppException

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# App
app = FastAPI(
    title="Expense App API", description="Backend", version="1.0.0", lifespan=lifespan
)


@app.exception_handler(AppException)
async def global_app_exception_handler(request: Request, exc: AppException):
    logger.error(
        "app_exception",
        extra={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "context": exc.context,
            "method": request.method,
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.context,
                "request_id": getattr(request.state, "request_id", None),
            },
        },
    )


app.include_router(auth_routes.router)
app.include_router(expense_routes.router)


# root to try
@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "message": "Welcome to Expense App!"}


if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
