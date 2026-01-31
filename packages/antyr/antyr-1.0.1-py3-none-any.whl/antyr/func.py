import mimetypes
import re
from pathlib import PurePosixPath
from urllib import parse

import httpx

FILENAME_PATTERN = re.compile(r'filename\s*=\s*"?([^"]+)"?', re.IGNORECASE)
CHARSET_FILENAME_PATTERN = re.compile(
    r"filename\*\s*=\s*([^']*)'[^']*'([^;]+)", re.IGNORECASE
)


def normalize_filename(filename: str) -> str:
    """
    Normalizes a filename into a filesystem-safe form.

    Characters commonly rejected by filesystems are replaced with underscores.
    Control characters are removed, and consecutive underscores are collapsed
    into a single underscore.

    Note:
        This function performs normalization only. It does not validate the
        resulting filename against platform-specific constraints.
    """

    filename = re.sub(r'[\\/:*?"<>|]', "_", filename)
    filename = re.sub(r"[\x00-\x1f\x7f]", "_", filename)
    return re.sub(r"\_+", "_", filename)


def detect_filename_from_context_disposition(
    disposition: str,
) -> str | None:
    """
    Extracts a filename from a Content-Disposition header value.

    Both standard filename parameters and RFC 5987 encoded filename parameters
    are supported. Charset-aware filenames are decoded according to the declared
    encoding, with a UTF-8 fallback when the charset is unknown.

    Args:
        disposition: Raw Content-Disposition header value.

    Returns:
        Decoded filename if present. None if no filename parameter is found.
    """

    name, charset = None, "utf-8"
    if match := CHARSET_FILENAME_PATTERN.search(disposition):
        charset, name = match.groups()

    if name is None:
        if match := FILENAME_PATTERN.search(disposition):
            name = match.group(1).strip()

    if name:
        name = parse.unquote_to_bytes(name)
        try:
            return name.decode(charset, errors="replace")
        except LookupError:
            return name.decode("utf-8", errors="replace")


def detect_file_extension_from_content_type(content_type: str) -> str:
    """
    Determine a file extension from a Content-Type header value.

    Parameters following the media type are ignored. The extension is resolved
    using the standard mimetypes registry.

    Args:
        content_type: Raw Content-Type header value.

    Returns:
        A file extension including the leading dot. Defaults to .txt if no
        mapping is found.
    """

    content_type = content_type
    content_type = content_type.split(";", 1)[0].strip()
    extension = mimetypes.guess_extension(content_type)
    return extension or ".txt"


def detect_filename_from_response(response: httpx.Response) -> str:
    """
    Determine a normalized filename from an HTTP response.

    The filename is resolved using the following precedence rules:

    1. Content-Disposition header, if present.
    2. The final path segment of the response URL.
    3. File extension inferred from the Content-Type header, if available.

    The resulting filename is always normalized before being returned.

    Args:
        response: HTTP response object.

    Returns:
        A normalized filename suitable for filesystem usage.
    """

    filename, ext = None, None
    if disposition := response.headers.get("Content-Disposition"):
        filename = detect_filename_from_context_disposition(disposition)

    if filename is None:
        filename = PurePosixPath(response.url.path).name

    if content_type := response.headers.get("Content-Type"):
        ext = detect_file_extension_from_content_type(content_type)

    if ext is not None and not filename.endswith(ext):
        return normalize_filename(filename + ext)

    return normalize_filename(filename)
