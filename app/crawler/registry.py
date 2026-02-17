from app.crawler.adapters.demo_platform import DemoPlatformAdapter
from app.crawler.adapters.demo_university import DemoUniversityAdapter
from app.crawler.adapters.iguopin_jobs import IGuoPinJobsAdapter
from app.crawler.adapters.job58_public import Job58PublicAdapter
from app.crawler.adapters.job51_public import Job51PublicAdapter
from app.crawler.adapters.remoteok_real import RemoteOKRealAdapter
from app.crawler.adapters.zhaopin_public import ZhaopinPublicAdapter
from app.crawler.adapters.zhipin_public import ZhiPinPublicAdapter
from app.crawler.base import SiteAdapter

REGISTRY: dict[str, type[SiteAdapter]] = {
    "demo_platform": DemoPlatformAdapter,
    "demo_university": DemoUniversityAdapter,
    "remoteok_real": RemoteOKRealAdapter,
    "iguopin_jobs": IGuoPinJobsAdapter,
    "zhipin_public": ZhiPinPublicAdapter,
    "zhaopin_public": ZhaopinPublicAdapter,
    "job51_public": Job51PublicAdapter,
    "job58_public": Job58PublicAdapter,
}


def get_adapter(source_code: str, config: dict | None = None) -> SiteAdapter:
    adapter_cls = REGISTRY.get(source_code)
    if adapter_cls is None:
        raise KeyError(f"No crawler adapter registered for source={source_code}")
    return adapter_cls(config=config)
