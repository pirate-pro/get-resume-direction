from app.crawler.adapters.demo_platform import DemoPlatformAdapter
from app.crawler.adapters.demo_university import DemoUniversityAdapter
from app.crawler.base import SiteAdapter

REGISTRY: dict[str, type[SiteAdapter]] = {
    "demo_platform": DemoPlatformAdapter,
    "demo_university": DemoUniversityAdapter,
}


def get_adapter(source_code: str) -> SiteAdapter:
    adapter_cls = REGISTRY.get(source_code)
    if adapter_cls is None:
        raise KeyError(f"No crawler adapter registered for source={source_code}")
    return adapter_cls()
