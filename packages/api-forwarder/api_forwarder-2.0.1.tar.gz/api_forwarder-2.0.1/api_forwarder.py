import asyncio
import json
from abc import ABC, abstractmethod
from functools import partial

import cloudscraper
import httpx


class BaseHttpClient(ABC):
    @abstractmethod
    async def request(self, method: str, url: str, **kwargs):
        pass

class Forwarder:
    def __init__(
        self,
        base_url: str,
        backend: str = "cloudscraper",
        client_options: dict | None = None,
        *,
        timeout = 10.0,
        retries = 0,
        retry_delay = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

        client_options = client_options or {}

        if backend == "httpx":
            self.client = HttpxClient(timeout=timeout, **client_options)
        elif backend == "cloudscraper":
            self.client = CloudscraperClient()
        else:
            raise ValueError(f"Unknown backend: {backend}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        close = getattr(self.client, "aclose", None)
        if callable(close):
            await close()

    async def request(self, method: str, path: str, **kwargs):
        url = self.base_url + path
        last_exc = None

        for attempt in range(self.retries + 1):
            try:
                return await asyncio.wait_for(
                    self.client.request(method, url, **kwargs),
                    timeout=self.timeout,
                )
            except Exception as e:
                last_exc = e
                if attempt < self.retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise ForwarderError(
                        f"Request failed after {self.retries + 1} attempts"
                    ) from e

    async def get(self, path: str, **kwargs):
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.request("POST", path, **kwargs)

class ForwarderResponse:
    def __init__(self, *, status_code, headers, content, url=None):
        self.status_code = status_code
        self.headers = dict(headers)
        self.content = content
        self.url = url

    @property
    def text(self) -> str:
        return self.content.decode(self._encoding(), errors="replace")

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPStatusError(
                status_code=self.status_code,
                text=self.text,
                url=self.url,
            )
        return self

    def _encoding(self) -> str:
        ct = self.headers.get("content-type", "")
        if "charset=" in ct:
            return ct.split("charset=")[-1].split(";")[0]
        return "utf-8"


class HttpxClient(BaseHttpClient):
    def __init__(self, **opts):
        self.client = httpx.AsyncClient(**opts)

    async def request(self, method, url, **kwargs):
        r = await self.client.request(method, url, **kwargs)
        return ForwarderResponse(
            status_code=r.status_code,
            headers=r.headers,
            content=r.content,
            url=str(r.url),
        )

    async def aclose(self):
        await self.client.aclose()


class CloudscraperClient(BaseHttpClient):
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def _sync(self, method, url, **kwargs):
        return self.scraper.request(method, url, **kwargs)

    async def request(self, method, url, **kwargs):
        loop = asyncio.get_running_loop()
        r = await loop.run_in_executor(
            None, partial(self._sync, method, url, **kwargs)
        )
        return ForwarderResponse(
            status_code=r.status_code,
            headers=r.headers,
            content=r.content,
            url=r.url,
        )

    async def aclose(self):
        pass

class ForwarderError(Exception):
    pass

class HTTPStatusError(ForwarderError):
    def __init__(self, status_code: int, text: str, url: str | None = None):
        self.status_code = status_code
        self.text = text
        self.url = url
        super().__init__(f"HTTP {status_code} error for {url}")