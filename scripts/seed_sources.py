import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.models.source import Source

SOURCES = [
    {
        "code": "demo_platform",
        "name": "Demo Recruiting Platform",
        "source_type": "platform",
        "enabled": True,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "*/30 * * * *",
            "throttle": {"qps": 1.0, "concurrency": 2, "jitter_ms": 200},
            "retry": {"max_attempts": 3, "backoff_seconds": 1.0},
            "allow_paths": ["/jobs"],
            "deny_paths": ["/captcha", "/login"],
        },
    },
    {
        "code": "demo_university",
        "name": "Demo University Career Site",
        "source_type": "university",
        "enabled": True,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "15 */1 * * *",
            "throttle": {"qps": 0.5, "concurrency": 1, "jitter_ms": 500},
            "retry": {"max_attempts": 2, "backoff_seconds": 2.0},
            "allow_paths": ["/career", "/notice"],
            "deny_paths": ["/captcha", "/login"],
        },
    },
]


async def main() -> None:
    async with SessionLocal() as session:
        for source in SOURCES:
            stmt = insert(Source).values(**source)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Source.code],
                set_={
                    "name": source["name"],
                    "source_type": source["source_type"],
                    "enabled": source["enabled"],
                    "robots_allowed": source["robots_allowed"],
                    "config_json": source["config_json"],
                },
            )
            await session.execute(stmt)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
