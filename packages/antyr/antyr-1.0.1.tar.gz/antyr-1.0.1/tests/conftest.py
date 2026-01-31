from contextlib import asynccontextmanager

import pytest
import trio
from hypothesis import settings

from .servers import TestServer, http_handler, stem_control_handler

settings.register_profile("short", max_examples=10)
settings.register_profile("long", max_examples=200)


@pytest.fixture(scope="session")
def http_server():
    @asynccontextmanager
    async def _server():
        test_server = TestServer(http_handler)
        async with trio.open_nursery() as nursery:
            nursery.start_soon(test_server.serve)
            await test_server.ready.wait()
            yield test_server
            nursery.cancel_scope.cancel()

    return _server


@pytest.fixture(scope="session")
def control_server():
    @asynccontextmanager
    async def _server():
        test_server = TestServer(stem_control_handler, port=9051)
        async with trio.open_nursery() as nursery:
            nursery.start_soon(test_server.serve)
            await test_server.ready.wait()
            yield test_server
            nursery.cancel_scope.cancel()

    return _server
