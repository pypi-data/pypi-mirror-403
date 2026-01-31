import socket
from types import TracebackType
from typing import Any, Dict, Mapping, Type

import httpx
import trio
from stem import Signal
from stem.control import Controller

from .constants import MAX_REDIRECTS, TIMEOUT
from .results import FetchResult


class HttpCrawler:
    """
    Asynchronous HTTP crawler built on top of httpx.

    Provides a lightweight wrapper around `httpx.AsyncClient` with
    a constrained, result-oriented fetch API.

    The crawler manages client lifecycle through an asynchronous
    context manager and exposes request execution via `FetchResult`.
    """

    def __init__(
        self,
        base_url: str = "",
        *,
        timeout: float = TIMEOUT,
        auth: httpx.Auth | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: Dict[str, str] | httpx.Cookies | None = None,
        follow_redirects: bool = True,
        max_redirects: int = MAX_REDIRECTS,
        proxy: str | httpx.URL | httpx.Proxy | None = None,
    ):
        self._base_url = base_url
        self._proxy = proxy
        self._timeout = timeout
        self._cookies = cookies or {}
        self._client = httpx.AsyncClient(
            auth=auth,
            params=params,
            headers=headers,
            cookies=self._cookies,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
            base_url=base_url,
            proxy=proxy,
            timeout=timeout,
        )

    async def __aenter__(self) -> "HttpCrawler":
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self, exc_type: Type[BaseException], exc: BaseException, tb: TracebackType
    ) -> None:
        await self._client.__aexit__(exc_type, exc, tb)

    @property
    def cookies(self) -> httpx.Cookies:
        return self._client.cookies

    def fetch(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: Dict[str, str] | None = None,
        auth: httpx.Auth | None = None,
        follow_redirects: bool = True,
        timeout: float | None = None,
    ) -> FetchResult:
        """
        Prepares an HTTP GET request.

        Returns a `FetchResult` wrapper that defers request execution
        until awaited or otherwise resolved.

        Request-specific parameters override client defaults.
        """

        return FetchResult(self._client.get).init(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout if timeout is not None else self._timeout,
        )

    async def rotate_ip(self, host: str, password: str) -> None:
        """
        Requests a new Tor exit IP address.

        Sends a `NEWNYM` signal to the Tor control port associated
        with the given host.

        The operation is executed in a worker thread to avoid
        blocking the event loop.
        """

        def send_reset_ip_signal():
            host_ip = socket.gethostbyname(host)
            with Controller.from_port(address=host_ip) as controller:
                controller.authenticate(password=password)
                controller.signal(Signal.NEWNYM)  # type: ignore[attr-defined]

        await trio.to_thread.run_sync(send_reset_ip_signal)
