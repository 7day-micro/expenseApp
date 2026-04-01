from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.db.database import engine
from src.models import Base
from src.auth import routes as auth_routes
from src.config import settings


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

app.include_router(auth_routes.router)


# root to try
@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "message": "Welcome to Expense App!"}


if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    errors = exc.errors()
    for error in errors:
        if "input" in error:
            del error["input"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": errors},
    )
