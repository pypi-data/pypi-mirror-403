import io
import mimetypes
import zipfile
from typing import Sequence, Tuple

import pytest
import trio
from hypothesis import given
from hypothesis import strategies as st

from antyr.func import normalize_filename
from antyr.zip import AsyncZipFile, Extractor, OpeningAbortError

from .strategies import filenames

# --- Zip file strategies ---

ZipData = Tuple[io.BytesIO, str, bytes]
MultipleZipData = Tuple[io.BytesIO, Sequence[str], Sequence[bytes]]


@st.composite
def zip_data(draw) -> ZipData:
    buf = io.BytesIO()
    content = draw(st.binary(min_size=1, max_size=32))
    filename = draw(filenames())
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, content)
    buf.seek(0)
    return buf, filename, content


@st.composite
def multiple_zip_data(draw) -> MultipleZipData:
    buf = io.BytesIO()
    files = draw(st.lists(filenames(), min_size=2, max_size=5, unique=True))
    contents = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            content = draw(st.binary(min_size=1, max_size=32))
            zf.writestr(filename, content)
            contents.append((filename, content))
    buf.seek(0)
    return buf, files, contents


@pytest.fixture
def zip_with_dir():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dir/", b"")
        zf.writestr("dir/file.txt", b"data")
    buf.seek(0)
    return buf


@pytest.mark.trio
@given(zip_data())
async def test_double_open_raises(data: ZipData):
    buf, _, _ = data
    async with AsyncZipFile(buf) as zf:
        with pytest.raises(RuntimeError):
            await zf.open()


@pytest.mark.trio
@given(multiple_zip_data())
async def test_files_iteration(data: MultipleZipData):
    buf, names, _ = data
    async with AsyncZipFile(buf) as zf:
        _names = {m.filename async for m in zf.files()}
        assert _names == set(names)


@pytest.mark.trio
async def test_directories_skipped(zip_with_dir):
    async with AsyncZipFile(zip_with_dir) as zf:
        files = [m.filename async for m in zf.files()]
        assert files == ["dir/file.txt"]


@pytest.mark.trio
@given(zip_data())
async def test_files_before_open(data: ZipData):
    buf, _, _ = data
    zf = AsyncZipFile(buf)
    with pytest.raises(RuntimeError):
        await anext(zf.files())


@pytest.mark.trio
@given(zip_data())
async def test_files_after_close(data: ZipData):
    buf, _, _ = data
    zf = AsyncZipFile(buf)
    await zf.open()
    await zf.close()
    with pytest.raises(RuntimeError):
        await anext(zf.files())


@pytest.mark.trio
@given(zip_data())
async def test_files_fails_with_bad_file_opened(data: ZipData):
    _, _, content = data
    zf = AsyncZipFile(io.BytesIO(content))

    with pytest.raises(zipfile.BadZipFile):
        await zf.open()

    with pytest.raises(RuntimeError):
        await anext(zf.files())


@pytest.mark.trio
@given(zip_data())
async def test_close_without_open(data: ZipData):
    buf, _, _ = data
    zf = AsyncZipFile(buf)
    await zf.close()


# --- Member tests ---


@pytest.mark.trio
@given(zip_data())
async def test_member_read_all(data: ZipData):
    buf, _, content = data
    async with AsyncZipFile(buf) as zf:
        member = await anext(zf.files())
        async with member:
            _data = b"".join([c async for c in member.chunks()])
            assert _data == content


@pytest.mark.trio
@given(zip_data())
async def test_member_chunk_sizes(data: ZipData):
    buf, _, content = data
    async with AsyncZipFile(buf) as zf:
        member = await anext(zf.files())
        async with member:
            _data = b"".join([c async for c in member.chunks(2)])
            assert _data == content


@pytest.mark.trio
@given(zip_data())
async def test_member_requires_open(data: ZipData):
    buf, _, _ = data
    async with AsyncZipFile(buf) as zf:
        member = await anext(zf.files())
        with pytest.raises(RuntimeError):
            await anext(member.chunks())


@pytest.mark.trio
@given(zip_data())
async def test_member_double_open_forbidden(data: ZipData):
    buf, _, _ = data
    async with AsyncZipFile(buf) as zf:
        member = await anext(zf.files())
        async with member:
            with pytest.raises(RuntimeError):
                await member.open()


@pytest.mark.trio
@given(zip_data())
async def test_member_wait_opened_abort(data: ZipData):
    buf, _, _ = data
    async with AsyncZipFile(buf) as zf:
        member = await anext(zf.files())
        with trio.move_on_after(0):
            await member.open()

        with pytest.raises(OpeningAbortError):
            await anext(member.chunks())


@pytest.mark.trio
@given(zip_data())
async def test_member_close_without_open(data: ZipData):
    buf, _, _ = data
    async with AsyncZipFile(buf) as zf:
        member = await anext(zf.files())
        await member.close()


# --- Extractor tests ---


@pytest.mark.trio
@given(multiple_zip_data())
async def test_extractor_basic(data: MultipleZipData):
    buf, names, _ = data
    names = {normalize_filename(x) for x in names}
    extractor = Extractor(buf)
    async with extractor:
        _names = {c.path async for c in extractor.extract()}
        assert _names == names


@pytest.mark.trio
@given(zip_data())
async def test_content_type_filter(data: ZipData):
    buf, filename, _ = data
    extension = filename.split(".")[-1]
    content_type = mimetypes.types_map.get(extension) or "plain/text"
    extractor = Extractor(buf)
    async with extractor:
        async for chunk in extractor.extract(content_types=[content_type]):
            assert chunk.path == filename


@pytest.mark.trio
@given(zip_data())
async def test_max_file_size(data: ZipData):
    buf, _, _ = data
    extractor = Extractor(buf)
    async with extractor:
        with pytest.raises(ValueError):
            await anext(extractor.extract(max_file_size=0))


@pytest.mark.trio
async def test_compression_ratio_guard():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bomb.txt", b"A" * 10_000)
    buf.seek(0)

    extractor = Extractor(buf)
    async with extractor:
        with pytest.raises(ValueError):
            await anext(extractor.extract(max_compression_ratio=1.5))


@pytest.mark.trio
@given(zip_data())
async def test_extract_with_not_presented_content_type(data: ZipData):
    buf, _, _ = data
    extractor = Extractor(buf)
    async with extractor:
        chunks = [c async for c in extractor.extract(content_types=["unknown"])]
    assert len(chunks) == 0
