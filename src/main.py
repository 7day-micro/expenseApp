from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import status
from fastapi.exceptions import RequestValidationError

from src.auth import routes as auth_routes
from src.domain.expense import routes as expense_routes
from src.domain.budget import routes as budget_routes
from src.domain.category import routes as category_routes
from src.config import settings
from src.exceptions import AppException
import uuid

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


# App
app = FastAPI(
    title="Expense App API", description="Backend", version="1.0.0", lifespan=lifespan
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppException)
async def global_app_exception_handler(request: Request, exc: AppException):
    logger.error(
        "app_exception",
        extra={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            # "message": exc.message, # REMOVE , BY ERROR @Deiv888
            "context": str(exc.context),
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
app.include_router(budget_routes.router)
app.include_router(category_routes.router)


# root to try
@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "message": "Welcome to Expense App!"}


if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )


# new handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        # secure log
        logger.warning(f"Validation error occurred on endpoint: {request.url.path}")

        errors = exc.errors()
        for error in errors:
            if "input" in error:
                del error["input"]
            if "ctx" in error:
                del error["ctx"]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,  # or HTTP_422_UNPROCESSABLE_ENTITY
            content={"detail": errors},
        )
    except Exception as e:
        logger.error(f"Critical failure in validation handler: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": [{"msg": "Validation error (details hidden for security)"}]
            },
        )
