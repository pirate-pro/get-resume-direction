from abc import ABC, abstractmethod

from app.crawler.types import NormalizedJob, RawJob


class SiteAdapter(ABC):
    source_code: str

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def fetch_list(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_detail(self, list_item: dict) -> dict | str:
        raise NotImplementedError

    @abstractmethod
    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: RawJob) -> NormalizedJob:
        raise NotImplementedError

    async def crawl(self) -> list[NormalizedJob]:
        output: list[NormalizedJob] = []
        for item in await self.fetch_list():
            detail = await self.fetch_detail(item)
            raw = self.parse_raw_job(item, detail)
            output.append(self.normalize(raw))
        return output
