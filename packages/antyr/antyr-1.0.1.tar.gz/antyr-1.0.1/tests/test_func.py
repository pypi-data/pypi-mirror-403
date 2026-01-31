import mimetypes
import string
from urllib.parse import quote, urljoin

import httpx
import pytest
from hypothesis import given
from hypothesis import provisional as stp
from hypothesis import strategies as st

from antyr.func import (
    detect_file_extension_from_content_type,
    detect_filename_from_context_disposition,
    detect_filename_from_response,
    normalize_filename,
)

from .strategies import EMPTY_NAMES, EXTENSIONS, cyrillic, extensions, filenames, greek

FORBIDDEN = set('<>:"/\\|?*\x00\x1f\x7f')


# --- Media type and extension strategies ---

token = st.text(alphabet=string.ascii_lowercase + string.digits + "-", min_size=1)
random_media_types = st.builds(lambda t, s: f"{t}/{s}", t=token, s=token)
strict_media_types = st.sampled_from("".join(mimetypes.types_map.values()))
mixed_media_types = st.one_of(random_media_types, strict_media_types)


# --- URL strategies ---

url_chars = st.one_of(
    st.sampled_from(string.ascii_letters + string.digits + "._-~()!$&',;=@+"),
    cyrillic,
    greek,
).filter(lambda x: x not in EMPTY_NAMES)


@st.composite
def urls(draw):
    base_url = draw(stp.urls())
    name = draw(st.text(url_chars, min_size=1))
    extension = draw(extensions)
    return urljoin(base_url, f"{name}.{extension}")


# --- Common strategies ---

mixed_filenames = st.one_of(filenames(), urls())


# --- Normalization tests ---


@given(mixed_filenames)
def test_normalize_removes_forbidden_chars(name):
    normalized = normalize_filename(name)
    assert not any(ch in FORBIDDEN for ch in normalized)


@given(mixed_filenames)
def test_normalize_is_idempotent(name):
    a = normalize_filename(name)
    b = normalize_filename(a)
    assert a == b


# --- Content Disposition tests ---


@pytest.mark.parametrize(
    "header",
    [
        "attachment; filename=%s",
        "attachment; filename = %s",
        "attachment; filename*=UTF-8''%s",
        "attachment; filename* = UNKNOWN''%s",
    ],
)
@given(filenames())
def test_detect_filename_from_content_disposition(header, filename):
    disposition = header % quote(filename.encode())
    assert detect_filename_from_context_disposition(disposition) == filename


@given(mixed_media_types)
def test_detect_extension_from_content_type(content_type):
    extension = detect_file_extension_from_content_type(content_type)
    assert extension in EXTENSIONS


@pytest.mark.parametrize(
    "header",
    [
        "attachment; filename=%s",
        "attachment; filename = %s",
        "attachment; filename*=UTF-8''%s",
        "attachment; filename* = UNKNOWN''%s",
    ],
)
@given(filenames())
def test_detect_filename_from_response_content_disposition(header, filename):
    disposition = header % quote(filename.encode())
    response = httpx.Response(
        200,
        headers={"Content-Disposition": disposition},
        request=httpx.Request("GET", "http://example.com"),
    )
    assert detect_filename_from_response(response) == normalize_filename(filename)


@pytest.mark.parametrize(
    "header",
    [
        "attachment; filename=%s",
        "attachment; filename = %s",
        "attachment; filename*=UTF-8''%s",
        "attachment; filename* = UNKNOWN''%s",
    ],
)
@given(filenames(), strict_media_types)
def test_detect_filename_from_response_contennt_disposition_with_strinct_content_type(
    header, filename, content_type
):
    ext = mimetypes.guess_extension(content_type) or ""
    disposition = header % quote(filename.encode())
    response = httpx.Response(
        200,
        headers={
            "Content-Disposition": disposition,
            "Content-Type": content_type,
        },
        request=httpx.Request("GET", "http://example.com"),
    )
    assert detect_filename_from_response(response).endswith(ext)


@pytest.mark.parametrize(
    "header",
    [
        "attachment; filename=%s",
        "attachment; filename = %s",
        "attachment; filename*=UTF-8''%s",
        "attachment; filename* = UNKNOWN''%s",
    ],
)
@given(filenames(), random_media_types)
def test_detect_filename_from_response_content_disposition_with_unknown_content_type(
    header, filename, content_type
):
    disposition = header % quote(filename.encode())
    response = httpx.Response(
        200,
        headers={
            "Content-Disposition": disposition,
            "Content-Type": content_type,
        },
        request=httpx.Request("GET", "http://example.com"),
    )
    assert detect_filename_from_response(response).endswith(".txt")


# --- URL tests ---


@given(urls())
def test_detect_filename_from_response_url(url):
    filename = normalize_filename(url.split("/")[-1])
    response = httpx.Response(200, request=httpx.Request("GET", url))
    assert detect_filename_from_response(response) == normalize_filename(filename)


@given(urls(), strict_media_types)
def test_detect_filename_from_response_url_with_strict_content_type(url, content_type):
    ext = mimetypes.guess_extension(content_type) or ""
    response = httpx.Response(
        200,
        headers={"Content-Type": content_type},
        request=httpx.Request("GET", url),
    )
    assert detect_filename_from_response(response).endswith(ext)


@given(urls(), random_media_types)
def test_detect_filename_from_response_url_with_unknown_content_type(url, content_type):
    response = httpx.Response(
        200,
        headers={"Content-Type": content_type},
        request=httpx.Request("GET", url),
    )
    assert detect_filename_from_response(response).endswith(".txt")
