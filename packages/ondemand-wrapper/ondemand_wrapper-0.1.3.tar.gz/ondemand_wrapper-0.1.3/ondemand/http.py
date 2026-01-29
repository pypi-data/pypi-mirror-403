import httpx
from .errors import HTTPError


class AsyncHTTP:
    def __init__(self, api_key: str, timeout: float):
        self._client = httpx.AsyncClient(
            headers={"apikey": api_key},
            timeout=timeout,
        )

    async def post(self, url: str, **kw):
        r = await self._client.post(url, **kw)
        if r.status_code >= 400:
            raise HTTPError(r.status_code, r.text)
        return r

    async def close(self):
        await self._client.aclose()
