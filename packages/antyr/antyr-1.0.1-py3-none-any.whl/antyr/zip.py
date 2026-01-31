import mimetypes
import zipfile
from types import TracebackType
from typing import IO, AsyncGenerator, Sequence, Type

import trio
from typing_extensions import Self

from .func import normalize_filename
from .streaming import Chunk, ContentStream


class OpeningAbortError(Exception):
    """
    Raised when an asynchronous ZIP open operation is aborted.

    Indicates that an attempt to open a ZIP file or one of its
    members did not complete successfully and was explicitly marked as aborted.
    """

    pass


class AsyncZipMember:
    """
    Asynchronous wrapper around a single file inside a ZIP archive.

    Provides an async-friendly interface for opening, reading, and closing
    individual archive members.

    The underlying file handle is opened in a worker thread and guarded by
    explicit state tracking. Reads are protected by a lock to prevent concurrent
    access. Cleanup is safe under cancellation.

    A member must be opened before reading and should be closed explicitly, or
    via an async context manager, once processing is complete.
    """

    def __init__(self, info: zipfile.ZipInfo, file: zipfile.ZipFile) -> None:
        self._info = info
        self._file = file
        self._lock = trio.Lock()

        self._buffer: IO[bytes] | None = None

        self._is_open_called = False
        self._opened = trio.Event()
        self._aborted = trio.Event()

    async def __aenter__(self) -> Self:
        return await self.open()

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        await self.close()

    async def __wait_opened(self) -> None:
        async with trio.open_nursery() as nursery:

            async def wait_state_changed(event: trio.Event) -> None:
                await event.wait()
                nursery.cancel_scope.cancel()

            nursery.start_soon(wait_state_changed, self._opened)
            nursery.start_soon(wait_state_changed, self._aborted)

        if self._aborted.is_set():
            self._is_open_called = False
            raise OpeningAbortError("Opening zip member was aborted")

    @property
    def filename(self) -> str:
        return self._info.filename

    @property
    def compress_size(self) -> int:
        return self._info.compress_size

    @property
    def file_size(self) -> int:
        return self._info.file_size

    async def open(self) -> Self:
        """
        Opens the ZIP member asynchronously.

        The underlying file object is obtained in a worker thread to avoid
        blocking the Trio event loop.

        Raises:
            RuntimeError: If the member is already open or opening is in progress.
            OpeningAbortError: If the open operation is aborted.
            BaseException: Any unexpected error raised while opening the file.
        """

        if self._is_open_called:
            raise RuntimeError("File is already opened or opening in progress")

        self._is_open_called = True
        self._aborted = trio.Event()

        try:
            buffer = await trio.to_thread.run_sync(self._file.open, self._info)
            self._buffer = buffer
            self._opened.set()
        except BaseException:
            self._aborted.set()
            raise
        return self

    async def close(self) -> None:
        if not self._is_open_called:
            return

        await self.__wait_opened()

        if self._buffer is None:
            raise RuntimeError("File buffer was never opened")  # pragma: no cover

        with trio.CancelScope(shield=True):
            await trio.to_thread.run_sync(self._buffer.close)
            self._is_open_called = False
            self._opened = trio.Event()
            self._buffer = None

    async def chunks(
        self, chunk_size: int | None = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Streams the contents of the ZIP member as byte chunks.

        Args:
            chunk_size: Maximum number of bytes per chunk. If not provided, the
                file is read until EOF in a single call.

        Yields:
            Byte chunks read from the ZIP member.

        Raises:
            RuntimeError: If the member was not opened before reading.
            OpeningAbortError: If the opening process was aborted.
        """

        if not self._is_open_called:
            raise RuntimeError("File was not opened")

        await self.__wait_opened()

        if self._buffer is None:
            raise RuntimeError("File buffer was never opened")  # pragma: no cover

        while True:
            async with self._lock:
                data = await trio.to_thread.run_sync(
                    self._buffer.read, chunk_size or -1
                )

            if not data:
                break

            yield data


class AsyncZipFile:
    """
    Asynchronous reader for ZIP archives.

    Provides controlled, non-blocking access to ZIP files by opening and closing
    the underlying `zipfile.ZipFile` in worker threads.

    A strict open/close lifecycle is enforced. Resource cleanup is safe under
    cancellation. Archive entries are exposed through an asynchronous interface.
    """

    def __init__(
        self,
        file: IO[bytes],
        *,
        timeout: float | None = None,
    ) -> None:
        self._file = file
        self._timeout = timeout

        self._zip_file: zipfile.ZipFile | None = None

        self._is_open_called = False
        self._opened = trio.Event()
        self._aborted = trio.Event()

    async def __aenter__(self) -> Self:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        await self.close()

    async def __wait_opened(self) -> None:
        async with trio.open_nursery() as nursery:

            async def wait_state_changed(event: trio.Event) -> None:
                await event.wait()
                nursery.cancel_scope.cancel()

            nursery.start_soon(wait_state_changed, self._opened)
            nursery.start_soon(wait_state_changed, self._aborted)

        if self._aborted.is_set():
            raise OpeningAbortError("Opening zip file was aborted")

    async def open(self) -> Self:
        """
        Opens the ZIP archive asynchronously.

        The archive is initialized in a worker thread to avoid blocking the Trio
        event loop.

        Raises:
            RuntimeError: If the archive is already open or opening is in progress.
            OpeningAbortError: If the open operation is aborted.
            BaseException: Any unexpected error during ZIP initialization.
        """

        if self._is_open_called:
            raise RuntimeError("Zip file is already opened or opening in progress")

        self._is_open_called = True
        self._aborted = trio.Event()

        def open_zip() -> zipfile.ZipFile:
            return zipfile.ZipFile(self._file, "r")

        try:
            file = await trio.to_thread.run_sync(open_zip)
            self._zip_file = file
            self._opened.set()
        except BaseException:
            self._is_open_called = False
            self._aborted.set()
            raise
        return self

    async def close(self) -> None:
        if not self._is_open_called:
            return

        await self.__wait_opened()

        if self._zip_file is None:
            raise RuntimeError("Zip file was never opened")  # pragma: no cover

        with trio.CancelScope(shield=True):
            await trio.to_thread.run_sync(self._zip_file.close)
            self._is_open_called = False
            self._opened = trio.Event()
            self._zip_file = None

    async def files(self) -> AsyncGenerator[AsyncZipMember, None]:
        """
        Iterates over file entries in the ZIP archive.

        Directory entries are skipped. Each yielded object represents a single
        file inside the archive and must be opened explicitly before reading.

        Yields:
            AsyncZipMember instances for each non-directory entry.

        Raises:
            RuntimeError: If the ZIP archive has not been opened.
        """

        if not self._is_open_called:
            raise RuntimeError("Zip file was not opened")

        await self.__wait_opened()

        if self._zip_file is None:
            raise RuntimeError("Zip file was never opened")  # pragma: no cover

        infolist = await trio.to_thread.run_sync(self._zip_file.infolist)
        for info in infolist:
            if info.is_dir():
                continue
            yield AsyncZipMember(info, self._zip_file)


class Extractor:
    """
    High-level, streaming ZIP extractor.

    Wraps `AsyncZipFile` and exposes a simplified interface for extracting ZIP
    contents as a stream of `Chunk` objects.

    Extraction is sequential and streaming. Common safety checks are supported,
    including MIME-based filtering, file size limits, and basic ZIP bomb
    protection.
    """

    def __init__(self, file: IO[bytes]) -> None:
        self._file = AsyncZipFile(file)

    async def __aenter__(self) -> "Extractor":
        await self._file.open()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._file.close()

    async def extract(
        self,
        *,
        content_types: Sequence[str] | None = None,
        max_compression_ratio: float | None = None,
        max_file_size: int | None = None,
        chunk_size: int | None = None,
    ) -> ContentStream:
        """
        Extracts files from the ZIP archive as a stream of chunks.

        Files are processed sequentially. Each file is opened, validated against
        the provided constraints, streamed as chunks, and closed before the next
        entry is processed.

        Args:
            content_types: Optional list of allowed MIME types. Only files whose
                extensions match these types are extracted.
            max_compression_ratio: Maximum allowed ratio of uncompressed size to
                compressed size. Used as basic ZIP bomb protection.
            max_file_size: Maximum allowed uncompressed file size in bytes.
            chunk_size: Optional chunk size for streaming file contents.

        Yields:
            Chunk objects containing file path, content bytes, and byte offsets.

        Raises:
            ValueError: If a file exceeds size or compression constraints.

        Note:
            Filenames are normalized using `normalize_filename` to handle
            potentially invalid, inconsistent, or unsafe names stored in ZIP
            archives.
        """

        extensions = None
        if content_types is not None:
            extensions = [mimetypes.guess_extension(x) for x in content_types]
        async for member in self._file.files():
            filename = normalize_filename(member.filename)
            if extensions is not None and not any(
                filename.lower().endswith(ext) for ext in extensions if ext is not None
            ):
                continue

            if member.compress_size > 0:
                ratio = member.file_size / member.compress_size
                if max_compression_ratio is not None and ratio > max_compression_ratio:
                    raise ValueError(
                        f"File {filename} exceeds the maximum compression ratio: {ratio:.2f}"
                    )

            if max_file_size is not None and member.file_size > max_file_size:
                raise ValueError(f"File is too large: {filename}")

            async with member:
                total = 0

                async for chunk in member.chunks(chunk_size):
                    offset, length = total, len(chunk)
                    total += length
                    yield Chunk(
                        path=str(filename),
                        content=bytes(chunk),
                        offset=offset,
                        length=length,
                    )
