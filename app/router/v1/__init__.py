from app.router.v1.campus_events import router as campus_events_router
from app.router.v1.crawler import router as crawler_router
from app.router.v1.jobs import router as jobs_router
from app.router.v1.orders import router as orders_router
from app.router.v1.sources import router as sources_router
from app.router.v1.stats import router as stats_router

__all__ = ["campus_events_router", "crawler_router", "jobs_router", "orders_router", "sources_router", "stats_router"]
