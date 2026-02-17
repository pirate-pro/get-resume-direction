from abc import ABC, abstractmethod

from app.crawler.types_event import NormalizedCampusEvent


class CampusEventAdapter(ABC):
    source_code: str

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def crawl(self) -> list[NormalizedCampusEvent]:
        raise NotImplementedError
