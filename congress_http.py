import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

CONCURRENCY = 100
MAX_ATTEMPTS = 5
RETRY_STATUSES = {429, 503}


def new_client() -> httpx.AsyncClient:
    """Shared connection pool; follow redirects to match requests."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0),
        follow_redirects=True,
        limits=httpx.Limits(
            max_connections=CONCURRENCY * 2,
            max_keepalive_connections=CONCURRENCY,
        ),
    )


def new_semaphore() -> asyncio.Semaphore:
    """Cap in-flight requests across members and votes."""
    return asyncio.Semaphore(CONCURRENCY)


def _congress_params(params=None):
    merged = {"api_key": os.getenv("CONGRESS_API_KEY"), "format": "json"}
    if params:
        merged.update(params)
    return merged


class Progress:
    def __init__(self, label: str, total: int):
        self.label = label
        self.total = total
        self.done = 0
        self._lock = asyncio.Lock()

    async def tick(self):
        async with self._lock:
            self.done += 1
            if self.done == self.total or self.done % 25 == 0:
                print(f"{self.label} {self.done}/{self.total}", flush=True)


async def _request(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str, params=None):
    delay = 1.0
    last_response = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            async with sem:
                response = await client.get(url, params=params)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if attempt == MAX_ATTEMPTS - 1:
                raise
            print(f"{type(exc).__name__} on {url} (attempt {attempt + 1}/{MAX_ATTEMPTS})", flush=True)
            await asyncio.sleep(delay)
            delay *= 2
            continue
        if response.status_code in RETRY_STATUSES:
            last_response = response
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
            print(f"{response.status_code} on {url} (attempt {attempt + 1}/{MAX_ATTEMPTS}), retry in {wait:.0f}s", flush=True)
            await asyncio.sleep(wait)
            delay *= 2
            continue
        response.raise_for_status()
        return response
    if last_response is None:
        raise RuntimeError(f"GET {url} failed after {MAX_ATTEMPTS} attempts")
    last_response.raise_for_status()


async def get_json(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str, params=None):
    """GET JSON from Congress.gov with retries and a concurrency cap."""
    response = await _request(client, sem, url, params=_congress_params(params))
    return response.json()


async def get_text(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str):
    """GET a text/HTML body (GovInfo) with the same retry and concurrency rules."""
    response = await _request(client, sem, url)
    return response.text
