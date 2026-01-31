from io import BytesIO
from pathlib import Path
from typing import IO, Any, Callable, Coroutine, Dict, Mapping, Sequence

import httpx
from typing_extensions import Self

from .execution import LazyExecutionChain, LazyExecutionNode
from .files import Writer
from .func import detect_filename_from_response
from .streaming import Chunk, ContentStream
from .zip import Extractor


class ExtractResult(LazyExecutionChain[..., ContentStream]):
    """
    Execution chain producing a streamed extraction result.

    Represents a deferred extraction step that yields a content stream.
    Instances are typically attached to a preceding execution step that
    produces a binary input suitable for extraction.
    """

    def __init__(
        self, fn: Callable[[IO[bytes]], Coroutine[None, None, ContentStream]]
    ) -> None:
        super().__init__(fn)

    def save(
        self, base_path: str | Path = Path.cwd()
    ) -> LazyExecutionNode[[ContentStream], None]:
        """
        Persists extracted content to the filesystem.

        The returned execution node consumes a content stream and writes all
        yielded chunks under the provided base path.

        Args:
            base_path: Target directory for extracted files.

        Returns:
            Execution node performing the save operation.
        """

        async def save_function(stream: ContentStream) -> None:
            async with Writer(base_path) as writer:
                await writer.save(stream)

        return self.then(save_function)


class FetchResult(LazyExecutionChain[..., httpx.Response]):
    """
    Execution chain producing an HTTP response.

    Wraps a deferred HTTP request and exposes helpers for consuming the
    response body as a stream, an in-memory buffer, or an extracted archive.

    The response lifecycle is managed explicitly. The response is closed
    deterministically once consumption completes or aborts.
    """

    def __init__(
        self, fn: Callable[..., Coroutine[None, None, httpx.Response]]
    ) -> None:
        super().__init__(fn)

    async def __process_content_stream(
        self,
        response: httpx.Response,
        *,
        max_content_length: int | None = None,
        chunk_size: int | None = None,
    ) -> ContentStream:
        if max_content_length is not None:
            if content_length := response.headers.get("Content-Length"):
                if (
                    content_length.isdigit()
                    and int(content_length) > max_content_length
                ):
                    await response.aclose()
                    raise ValueError(f"File is too large: {content_length} bytes")

        async def generator() -> ContentStream:
            try:
                total = 0
                filename = detect_filename_from_response(response)
                async for chunk in response.aiter_bytes(chunk_size):
                    offset, length = total, len(chunk)
                    total += length
                    if max_content_length is not None and total > max_content_length:
                        await response.aclose()
                        raise ValueError(f"File is too large: {total} bytes")
                    yield Chunk(
                        path=filename,
                        content=chunk,
                        offset=offset,
                        length=length,
                    )
            finally:
                await response.aclose()

        return generator()

    async def __process_buffer(
        self,
        response: httpx.Response,
        *,
        max_content_length: int | None = None,
        chunk_size: int | None = None,
    ) -> IO[bytes]:
        if max_content_length is not None:
            if content_length := response.headers.get("Content-Length"):
                if (
                    content_length.isdigit()
                    and int(content_length) > max_content_length
                ):
                    await response.aclose()
                    raise ValueError(f"File is too large: {content_length} bytes")

        buf = BytesIO()
        try:
            total = 0
            async for chunk in response.aiter_bytes(chunk_size):
                total += len(chunk)
                if max_content_length is not None and total > max_content_length:
                    await response.aclose()
                    raise ValueError(f"File is too large: {total} bytes")
                buf.write(chunk)
            buf.seek(0)
        finally:
            await response.aclose()
        return buf

    def init(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: Dict[str, str] | None = None,
        auth: httpx.Auth | None = None,
        follow_redirects: bool = True,
        timeout: float | None = None,
    ) -> Self:
        """
        Initializes the underlying HTTP request.

        Args:
            url: Target URL.
            params: Optional query parameters.
            headers: Optional request headers.
            cookies: Optional cookies mapping.
            auth: Optional authentication handler.
            follow_redirects: Whether redirects are followed automatically.
            timeout: Optional request timeout.

        Returns:
            The current fetch result instance.
        """

        super().init(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )
        return self

    async def content_stream(
        self,
        *,
        max_content_length: int | None = None,
        chunk_size: int | None = None,
    ) -> ContentStream:
        """
        Consumes the response body as a streamed content generator.

        Args:
            max_content_length: Optional upper bound for total content size.
            chunk_size: Optional chunk size for streaming.

        Returns:
            Stream of content chunks.
        """

        return await self.then(
            self.__process_content_stream,
            max_content_length=max_content_length,
            chunk_size=chunk_size,
        )

    async def buffer(
        self,
        *,
        max_content_length: int | None = None,
        chunk_size: int | None = None,
    ) -> IO[bytes]:
        """
        Consumes the response body into an in-memory buffer.

        Args:
            max_content_length: Optional upper bound for total content size.
            chunk_size: Optional chunk size for reading.

        Returns:
            In-memory buffer containing the response body.
        """

        return await self.then(
            self.__process_buffer,
            max_content_length=max_content_length,
            chunk_size=chunk_size,
        )

    def extract(
        self,
        content_types: Sequence[str] | None = None,
        *,
        max_content_length: int | None = None,
        chunk_size: int | None = None,
        max_file_size: int | None = None,
        max_compression_ratio: float | None = None,
    ) -> ExtractResult:
        """
        Extracts archive contents from the response body.

        The response body is fully buffered before extraction. Files are
        processed sequentially and yielded as a content stream.

        Args:
            content_types: Optional allowed content types for extracted files.
            max_content_length: Optional upper bound for response size.
            chunk_size: Optional chunk size for reading and extraction.
            max_file_size: Optional upper bound for extracted file size.
            max_compression_ratio: Optional compression ratio limit.

        Returns:
            Extraction result producing extracted content.
        """

        nxt = self.then(
            self.__process_buffer,
            max_content_length=max_content_length,
            chunk_size=chunk_size,
        )

        async def extract_function(content: IO[bytes]) -> ContentStream:
            async def generator() -> ContentStream:
                async with Extractor(content) as extractor:
                    async for chunk in extractor.extract(
                        content_types=content_types,
                        max_file_size=max_file_size,
                        max_compression_ratio=max_compression_ratio,
                        chunk_size=chunk_size,
                    ):
                        yield chunk

            return generator()

        return ExtractResult(extract_function).attach(nxt)

    def save(
        self,
        base_path: str | Path = Path.cwd(),
        *,
        max_content_length: int | None = None,
        chunk_size: int | None = None,
    ) -> LazyExecutionNode[[ContentStream], None]:
        """
        Persists the response body directly to the filesystem.

        The response body is streamed and written incrementally.
        The response is closed once streaming completes or aborts.

        Args:
            base_path: Target directory for saved files.
            max_content_length: Optional upper bound for total content size.
            chunk_size: Optional chunk size for streaming.

        Returns:
            Execution node performing the save operation.
        """

        nxt = self.then(
            self.__process_content_stream,
            max_content_length=max_content_length,
            chunk_size=chunk_size,
        )

        async def save_function(stream: ContentStream) -> None:
            async with Writer(base_path) as writer:
                await writer.save(stream)

        return nxt.then(save_function)
