import pytest

from app.crawler.adapters.demo_platform import DemoPlatformAdapter


@pytest.mark.asyncio
async def test_demo_platform_adapter_returns_jobs() -> None:
    adapter = DemoPlatformAdapter()
    jobs = await adapter.crawl()
    assert len(jobs) >= 1
    assert jobs[0].title
