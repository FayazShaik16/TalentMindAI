from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config.config import settings
from app.core.logging.logging import logger
from app.core.middleware.middleware import setup_middleware
from app.core.feature_flags.feature_flags import feature_flags
from app.api.v1.routers import health, dataset, semantic, jobs, candidate_intelligence, candidate_evidence, ranking, explanation, dashboard
from app.schemas.responses import ErrorResponse, ErrorDetail, ResponseMetadata
from app.telemetry.metrics import telemetry

# Ensure AI orchestrator registers all agents on startup
import app.services.agents.job_agent
import app.services.agents.candidate_agent
import app.services.agents.evidence_agent
import app.services.agents.ranking_agent
import app.services.agents.explainability_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup log parameters
    logger.info("app_starting")
    
    from app.database.session import is_sqlite, engine
    if is_sqlite:
        logger.info("sqlite_detected_initializing_database")
        from app.database.models.base import Base
        from app.database.models import candidate, candidate_evidence, candidate_intelligence, dataset_management, explanation, job, ranking, workspace
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("sqlite_database_initialized_successfully")

    logger.info(
        "loaded_configuration",
        env=settings.APP_ENV,
        debug=settings.APP_DEBUG,
        database=settings.get_database_url.split("@")[-1] if "@" in settings.get_database_url else "SQLite Local",
    )
    logger.info(
        "active_feature_flags",
        semantic_search=feature_flags.is_enabled("semantic_search"),
        embedding_engine=feature_flags.is_enabled("embedding_engine"),
        behavior_engine=feature_flags.is_enabled("behavior_engine"),
        evidence_engine=feature_flags.is_enabled("evidence_engine"),
        analytics=feature_flags.is_enabled("analytics"),
        explainability=feature_flags.is_enabled("explainability"),
        knowledge_graph=feature_flags.is_enabled("knowledge_graph"),
        authentication=feature_flags.is_enabled("authentication"),
    )
    yield
    # Shutdown log parameters
    logger.info("app_stopping")
    try:
        from app.database.session import async_session_factory
        from app.services.dataset_management_service import dataset_mgmt_service
        async with async_session_factory() as db:
            await dataset_mgmt_service.reset_dataset(db)
        logger.info("database_cleared_on_shutdown")
    except Exception as e:
        logger.error("failed_to_clear_database_on_shutdown", error=str(e))

app = FastAPI(
    title="TalentMind AI Backend API",
    description="Candidate Intelligence Platform - Base Foundation Services",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    )

# Register custom middlewares
setup_middleware(app)

# Mount endpoints
app.include_router(health.router)
app.include_router(dataset.router)
app.include_router(dataset.root_router)
app.include_router(semantic.router)
app.include_router(semantic.root_router)
app.include_router(jobs.router)
app.include_router(candidate_intelligence.router)
app.include_router(candidate_evidence.router)
app.include_router(ranking.router)
app.include_router(explanation.router)
app.include_router(dashboard.router)


# Custom Exception Handlers returning standard Error envelopes
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    telemetry.increment_errors()
    req_id = getattr(request.state, "request_id", None)

    error_detail = ErrorDetail(
        code="VALIDATION_ERROR",
        message="Request parameters or payload failed validation criteria.",
        details=exc.errors()
    )
    response_content = ErrorResponse(
        error=error_detail,
        meta=ResponseMetadata(request_id=req_id)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content.model_dump()
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    req_id = getattr(request.state, "request_id", None)

    error_detail = ErrorDetail(
        code=f"HTTP_{exc.status_code}",
        message=exc.detail
    )
    response_content = ErrorResponse(
        error=error_detail,
        meta=ResponseMetadata(request_id=req_id)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content.model_dump()
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    telemetry.increment_errors()
    req_id = getattr(request.state, "request_id", None)
    logger.error("database_exception_caught", error=str(exc))

    error_detail = ErrorDetail(
        code="DATABASE_ERROR",
        message="An internal database transaction failed."
    )
    response_content = ErrorResponse(
        error=error_detail,
        meta=ResponseMetadata(request_id=req_id)
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content.model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    telemetry.increment_errors()
    req_id = getattr(request.state, "request_id", None)
    logger.error("unexpected_exception_caught", error=str(exc))

    error_detail = ErrorDetail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred."
    )
    response_content = ErrorResponse(
        error=error_detail,
        meta=ResponseMetadata(request_id=req_id)
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content.model_dump()
    )
