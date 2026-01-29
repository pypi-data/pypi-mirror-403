import anyio
from typing import Dict, List, AsyncIterator

from .config import OnDemandConfig
from .http import AsyncHTTP
from .resources.sessions import SessionResource
from .resources.media import MediaResource
from .resources.chat import ChatResource

from resources.sessions_sync import SessionResourceSync
from resources.media_sync import MediaResourceSync
from resources.chat_sync import ChatResourceSync


class _AsyncClient:
    def __init__(self, cfg: OnDemandConfig):
        self._http = AsyncHTTP(cfg.api_key, cfg.timeout)

        self.sessions = SessionResource(self._http)
        self.media = MediaResource(self._http)
        self.chat = ChatResource(self._http)

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self) -> "_AsyncClient":
        return self

    async def __aexit__(self, *_):
        await self.close()


class OnDemandClient:
    """
    Synchronous OnDemand client.

    Usage:
        client = OnDemandClient.from_env()
        session_id = client.sessions.create(...)
        client.close()
    """

    def __init__(self, cfg: OnDemandConfig):
        self._aio = _AsyncClient(cfg)

        self.sessions = SessionResourceSync(self._aio.sessions)
        self.media = MediaResourceSync(self._aio.media)
        self.chat = ChatResourceSync(self._aio.chat)

    @classmethod
    def from_env(cls) -> "OnDemandClient":
        return cls(OnDemandConfig.from_env())

    def close(self) -> None:
        anyio.run(self._aio.close)

    @classmethod
    def aio(cls) -> "_AsyncFacade":
        """
        Async entrypoint.

        Usage:
            async with OnDemandClient.aio() as client:
                await client.sessions.create(...)
        """
        return _AsyncFacade(_AsyncClient(OnDemandConfig.from_env()))


class _AsyncFacade:
    """
    Async client facade with the same resource layout as sync client.
    """

    def __init__(self, aio: _AsyncClient):
        self._aio = aio
        self.sessions = aio.sessions
        self.media = aio.media
        self.chat = aio.chat

    async def __aenter__(self) -> "_AsyncFacade":
        return self

    async def __aexit__(self, *_):
        await self._aio.close()
