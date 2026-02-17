from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.logging.config import configure_logging
from app.router.v1.campus_events import router as campus_events_router
from app.middlewares.request_context import RequestContextMiddleware
from app.middlewares.exception_handler import register_exception_handlers
from app.router.v1.crawler import router as crawler_router
from app.router.v1.jobs import router as jobs_router
from app.router.v1.orders import router as orders_router
from app.router.v1.sources import router as sources_router
from app.router.v1.stats import router as stats_router
from app.tasks.scheduler import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    if app.state.settings.scheduler_enabled:
        await scheduler_service.start()
    yield
    await scheduler_service.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(RequestContextMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    register_exception_handlers(app)

    app.include_router(jobs_router, prefix=settings.api_prefix, tags=["jobs"])
    app.include_router(campus_events_router, prefix=settings.api_prefix, tags=["campus-events"])
    app.include_router(orders_router, prefix=settings.api_prefix, tags=["orders"])
    app.include_router(stats_router, prefix=settings.api_prefix, tags=["stats"])
    app.include_router(crawler_router, prefix=settings.api_prefix, tags=["crawler"])
    app.include_router(sources_router, prefix=settings.api_prefix, tags=["sources"])

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        return {"status": "ready"}

    return app


app = create_app()
