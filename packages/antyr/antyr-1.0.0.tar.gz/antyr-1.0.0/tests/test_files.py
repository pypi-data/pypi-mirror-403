import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Sequence

import pytest
import trio
from hypothesis import given
from hypothesis import strategies as st

from antyr.files import Writer
from antyr.streaming import Chunk, ContentStream

from .strategies import filenames

# --- File strategies ---


@st.composite
def file_chunks(draw) -> Sequence[Chunk]:
    filename = draw(filenames())
    parts = draw(st.lists(st.binary(min_size=1, max_size=32), min_size=1, max_size=10))

    offset = 0
    chunks: List[Chunk] = []
    for data in parts:
        ln = len(data)
        chunks.append(Chunk(filename, data, offset, ln))
        offset += ln

    return chunks


@st.composite
def multiple_files_chunks(draw) -> Sequence[Chunk]:
    fls = draw(st.lists(filenames(), min_size=2, max_size=5, unique=True))
    chunks: List[Chunk] = []
    for filename in fls:
        parts = draw(
            st.lists(st.binary(min_size=1, max_size=32), min_size=1, max_size=5)
        )

        offset = 0
        for data in parts:
            ln = len(data)
            chunks.append(Chunk(filename, data, offset, ln))
            offset += ln

    return chunks


async def content_stream(chunks: Sequence[Chunk]) -> ContentStream:
    for chunk in chunks:
        yield chunk


@st.composite
def traversal_chunks(draw) -> Sequence[Chunk]:
    filename = draw(filenames())
    parts = draw(st.lists(st.binary(min_size=1, max_size=32), min_size=1, max_size=5))
    segments = draw(st.lists(st.just(".."), min_size=1, max_size=5))
    full_path = os.path.join(*segments, filename)

    offset = 0
    chunks: List[Chunk] = []
    for data in parts:
        ln = len(data)
        chunks.append(Chunk(full_path, data, offset, ln))
        offset += ln

    return chunks


@pytest.mark.trio
@given(file_chunks())
async def test_writer_writes_single_file(chunks: Sequence[Chunk]):
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        async with Writer(root) as writer:
            await writer.save(content_stream(chunks))

        expected: Dict[str, bytearray] = {}
        for chunk in chunks:
            expected.setdefault(chunk.path, bytearray())
            expected[chunk.path] += chunk.content

        for path, data in expected.items():
            result = (root / path).read_bytes()
            assert bytearray(result) == data


@pytest.mark.trio
@given(multiple_files_chunks())
async def test_writer_writes_multiple_files(chunks: Sequence[Chunk]):
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        async with Writer(root, concurrency_limit=2) as writer:
            await writer.save(content_stream(chunks))

        expected: Dict[str, bytearray] = {}
        for chunk in chunks:
            expected.setdefault(chunk.path, bytearray())
            expected[chunk.path] += chunk.content

        for path, data in expected.items():
            result = (root / path).read_bytes()
            assert bytearray(result) == data


@pytest.mark.trio
@given(traversal_chunks())
async def test_writer_rejects_path_traversal(chunks):
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        async with Writer(root) as writer:
            with pytest.raises(ExceptionGroup):
                await writer.save(content_stream(chunks))

        for chunk in chunks:
            assert not (root / chunk.path).exists()


@pytest.mark.trio
async def test_writer_does_not_hang_on_empty_stream(tmp_path):
    async with Writer(tmp_path) as writer:
        with trio.fail_after(1):
            await writer.save(content_stream([]))
