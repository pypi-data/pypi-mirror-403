import io
import zipfile
from typing import IO

import httpx
import pytest

from antyr.results import ExtractResult, FetchResult
from antyr.streaming import ContentStream
from antyr.zip import Extractor


@pytest.fixture
def simple_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a.txt", b"hello")
    buf.seek(0)
    return buf


@pytest.mark.trio
async def test_extract(simple_zip):

    async def extract(content: IO[bytes]) -> ContentStream:
        async def gen() -> ContentStream:
            async with Extractor(content) as extractor:
                async for chunk in extractor.extract():
                    yield chunk

        return gen()

    result = await ExtractResult(extract).init(simple_zip)
    data = b"".join([c.content async for c in result])
    assert data == b"hello"


@pytest.mark.trio
async def test_save_after_extract(simple_zip, tmp_path):
    async def extract(content: IO[bytes]) -> ContentStream:
        async def gen() -> ContentStream:
            async with Extractor(content) as extractor:
                async for chunk in extractor.extract():
                    yield chunk

        return gen()

    await ExtractResult(extract).init(simple_zip).save(tmp_path)
    saved_file = tmp_path / "a.txt"
    assert saved_file.exists()
    assert saved_file.read_bytes() == b"hello"


@pytest.mark.trio
async def test_fetch_content_stream_ok(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/ok")

            stream = await result.content_stream(chunk_size=5)
            data = b"".join([c.content async for c in stream])

            assert data == b"Hello, world!"


@pytest.mark.trio
async def test_fetch_content_stream_too_large(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/ok")

            with pytest.raises(ExceptionGroup):
                await result.content_stream(max_content_length=5)


@pytest.mark.trio
async def test_fetch_stream_too_large_with_no_headers(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/no-headers")

            with pytest.raises(ValueError):
                stream = await result.content_stream(max_content_length=5)
                await anext(stream)


@pytest.mark.trio
async def test_fetch_bytesio_ok(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/ok")

            buf = await result.buffer()
            data = buf.read()

            assert data == b"Hello, world!"


@pytest.mark.trio
async def test_fetch_buffer_too_large(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/ok")

            with pytest.raises(ExceptionGroup):
                await result.buffer(max_content_length=5)


@pytest.mark.trio
async def test_fetch_buffer_too_large_with_no_headers(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/no-headers")
            with pytest.raises(ExceptionGroup):
                await result.buffer(max_content_length=5)


@pytest.mark.trio
async def test_fetch_redirect(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/redirect")

            buf = await result.buffer()
            data = buf.read()

            assert data == b"Next"


@pytest.mark.trio
async def test_fetch_redirect_loop(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/redirect-loop")

            with pytest.raises(ExceptionGroup):
                await result.buffer()


@pytest.mark.trio
async def test_fetch_cookies(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = FetchResult(client.get).init("/cookies")

            buf = await result.buffer()
            data = buf.read()

            assert data == b"ok"
            assert client.cookies.get("session") == "abc123"


@pytest.mark.trio
async def test_extract_after_fetch(http_server):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            result = await FetchResult(client.get).init("/zip").extract()
            data = b"".join([c.content async for c in result])
            assert data == b"hello"


@pytest.mark.trio
async def test_save_after_fetch_and_extract(http_server, tmp_path):
    async with http_server() as server:
        async with httpx.AsyncClient(base_url=server.url) as client:
            await FetchResult(client.get).init("/zip").save(tmp_path)
            saved_file = tmp_path / "zip.zip"
            assert saved_file.exists()
