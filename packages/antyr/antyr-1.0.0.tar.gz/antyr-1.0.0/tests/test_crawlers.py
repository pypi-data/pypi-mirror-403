import pytest

from antyr.crawlers import HttpCrawler


@pytest.mark.trio
async def test_crawler_fetch_success(http_server):
    async with http_server() as srv:
        async with HttpCrawler(srv.url) as crawler:
            result = await crawler.fetch("/ok")
            assert result.status_code == 200
            assert result.text == "Hello, world!"


@pytest.mark.trio
async def test_crawler_fetch_404(http_server):
    async with http_server() as srv:
        async with HttpCrawler(srv.url) as crawler:
            request = await crawler.fetch("/missing")
            assert request.status_code == 404


@pytest.mark.trio
async def test_crawler_timeout(http_server):
    async with http_server() as srv:
        async with HttpCrawler(srv.url, timeout=0.1) as crawler:
            with pytest.raises(ExceptionGroup):
                await crawler.fetch("/slow")


@pytest.mark.trio
async def test_crawler_follow_redirects(http_server):
    async with http_server() as srv:
        async with HttpCrawler(srv.url) as crawler:
            response = await crawler.fetch("/redirect")
            assert response.status_code == 200
            assert response.text == "Next"


@pytest.mark.trio
async def test_crawler_redirects_loop(http_server):
    async with http_server() as srv:
        async with HttpCrawler(srv.url, max_redirects=3) as crawler:
            with pytest.raises(ExceptionGroup):
                await crawler.fetch("/redirect-loop")


@pytest.mark.trio
async def test_crawler_cookies(http_server):
    async with http_server() as srv:
        async with HttpCrawler(srv.url) as crawler:
            response = await crawler.fetch("/cookies")
            assert response.status_code == 200
            assert "session" in crawler.cookies
            assert crawler.cookies["session"] == "abc123"


@pytest.mark.trio
async def test_crawler_rotate_ip(control_server):
    async with control_server() as srv:
        async with HttpCrawler(
            "http://example.com", proxy="http://proxy.com"
        ) as crawler:
            await crawler.rotate_ip(srv.host, "password")
