from dataclasses import dataclass
from typing import AsyncGenerator, TypeAlias


@dataclass
class Chunk:
    """
    A contiguous slice of streamed binary content.

    A chunk represents a portion of a logical file or resource, carrying both
    its raw bytes and positional metadata within the original stream.
    """

    path: str
    content: bytes
    offset: int = 0
    length: int = 0


ContentStream: TypeAlias = AsyncGenerator[Chunk, None]
