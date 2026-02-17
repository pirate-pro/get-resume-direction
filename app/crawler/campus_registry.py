from app.crawler.adapters.iguopin_campus import IGuoPinCampusAdapter
from app.crawler.adapters.yingjiesheng_xjh import YingJieShengXjhAdapter
from app.crawler.campus_base import CampusEventAdapter

REGISTRY: dict[str, type[CampusEventAdapter]] = {
    "yingjiesheng_xjh": YingJieShengXjhAdapter,
    "iguopin_campus": IGuoPinCampusAdapter,
}


def get_campus_adapter(source_code: str, config: dict | None = None) -> CampusEventAdapter:
    adapter_cls = REGISTRY.get(source_code)
    if adapter_cls is None:
        raise KeyError(f"No campus crawler adapter registered for source={source_code}")
    return adapter_cls(config=config)
