import io
import zipfile
from typing import Awaitable, Callable

import httpx
import trio

Handler = Callable[[trio.SocketStream], Awaitable[None]]


def get_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a.txt", b"hello")
    buf.seek(0)
    return buf


class TestServer:
    def __init__(
        self, handler: Handler, host: str = "127.0.0.1", port: int = 0
    ) -> None:
        self.handler = handler
        self.host = host
        self.port = port
        self.ready = trio.Event()

    @property
    def url(self) -> httpx.URL:
        return httpx.URL(f"http://{self.host}:{self.port}/")

    async def serve(self) -> None:
        listeners = await trio.open_tcp_listeners(self.port, host=self.host)
        self.port = listeners[0].socket.getsockname()[1]
        self.ready.set()
        await trio.serve_listeners(self.handler, listeners)


async def http_handler(stream: trio.SocketStream) -> None:
    async with stream:
        request = await stream.receive_some(4096)

        request_line = request.split(b"\r\n", 1)[0]
        _, path, _ = request_line.split(b" ")
        if path == b"/ok":
            response = b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, world!"
        elif path == b"/zip":
            value = get_zip().getvalue()
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/zip\r\n"
                b"Content-Length: " + str(len(value)).encode() + b"\r\n\r\n" + value
            )
        elif path == b"/no-headers":
            response = b"HTTP/1.1 200 OK\r\n\r\nNo headers"
        elif path == b"/slow":
            await trio.sleep(1)
            response = b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nDone"
        elif path == b"/redirect":
            response = (
                b"HTTP/1.1 302 Found\r\nLocation: /next\r\nContent-Length: 0\r\n\r\n"
            )
        elif path == b"/next":
            response = b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nNext"
        elif path == b"/redirect-loop":
            response = b"HTTP/1.1 302 Found\r\nLocation: /redirect-loop\r\nContent-Length: 0\r\n\r\n"
        elif path == b"/cookies":
            response = b"HTTP/1.1 200 OK\r\nSet-Cookie: session=abc123\r\nContent-Length: 2\r\n\r\nok"
        else:
            response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found"

        await stream.send_all(response)


async def stem_control_handler(stream: trio.SocketStream) -> None:
    async with stream:
        while True:
            buffer = await stream.receive_some(4096)

            for line in buffer.decode().split("\r\n"):
                if not line:
                    continue

                if line.startswith("PROTOCOLINFO"):
                    response = (
                        b"250-PROTOCOLINFO 1\r\n"
                        b"250-AUTH METHODS=HASHEDPASSWORD\r\n"
                        b'250-VERSION Tor="0.4.8.0"\r\n'
                        b"250 OK\r\n"
                    )
                elif line.startswith("AUTHENTICATE"):
                    _, raw = line.split(" ", 1)
                    password = raw.strip().strip('"')
                    if password:
                        response = b"250 OK\r\n"
                    else:
                        response = b"515 Authentication failed\r\n"
                elif line == "SIGNAL NEWNYM":
                    response = b"250 OK\r\n"
                else:
                    response = b"500 Unknown command\r\n"

                await stream.send_all(response)
