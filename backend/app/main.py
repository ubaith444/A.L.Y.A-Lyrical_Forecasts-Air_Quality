import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Database
from app.core.errors import ApiError
from app.core.logging import configure_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging(settings.log_level)
    Database(settings.database_path).initialize()
    yield


app = FastAPI(
    title="Alya Weather API",
    description="Lyrical Forecasts & Air Quality backend environment",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logging.getLogger(__name__).exception(
            "Unhandled request error", extra={"request_id": request_id}
        )
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "request_id": request_id,
                }
            },
        )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(
        round((time.perf_counter() - started_at) * 1000, 2)
    )
    logging.getLogger("alya.request").info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": float(response.headers["X-Response-Time-Ms"]),
        },
    )
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(
                    request.state, "request_id", request.headers.get("X-Request-ID")
                ),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": exc.errors(),
                "request_id": getattr(
                    request.state, "request_id", request.headers.get("X-Request-ID")
                ),
            }
        },
    )


@app.get("/health", tags=["System"], include_in_schema=False)
async def legacy_health_check():
    return {"status": "healthy", "app": settings.app_name, "api_version": "v1"}
