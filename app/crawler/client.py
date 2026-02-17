import asyncio
import random
from urllib.parse import urlparse

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class CrawlerClient:
    def __init__(
        self,
        timeout_seconds: int = 20,
        retry_count: int = 3,
        qps: float = 1.0,
        jitter_ms: int = 100,
        allow_paths: list[str] | None = None,
        deny_paths: list[str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        proxy: str | None = None,
        trust_env: bool = False,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.qps = max(qps, 0.01)
        self.jitter_ms = jitter_ms
        self.allow_paths = allow_paths or []
        self.deny_paths = deny_paths or []
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers=headers,
            cookies=cookies,
            proxy=proxy,
            trust_env=trust_env,
        )

    def _allowed(self, url: str) -> bool:
        path = urlparse(url).path
        if any(path.startswith(prefix) for prefix in self.deny_paths):
            return False
        if self.allow_paths and not any(path.startswith(prefix) for prefix in self.allow_paths):
            return False
        return True

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def get(self, url: str) -> httpx.Response:
        if not self._allowed(url):
            raise PermissionError(f"Path is blocked by allow/deny rules: {url}")

        await asyncio.sleep((1.0 / self.qps) + random.uniform(0, self.jitter_ms / 1000.0))
        response = await self.client.get(url)
        response.raise_for_status()
        return response

    async def close(self) -> None:
        await self.client.aclose()
