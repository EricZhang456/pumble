import asyncio
import ssl
import time
import platform
from collections.abc import Iterable

from . import Mumble_pb2
from .mumble_version import MumbleVersion
from .mumble_tcp_connection import MumbleTCPConnection

# https://github.com/mumble-voip/mumble/blob/master/docs/dev/network-protocol/overview.md

class MumbleClient:
    def __init__(self,
                 username: str,
                 password: str | None=None,
                 tokens: Iterable[str] | None=None):
        self.username = username
        self.password = password
        self.tokens = tokens
        self._connected = False
        self._ticker_task: asyncio.Task | None = None
        self._tcp_connection: MumbleTCPConnection | None = None

    async def connect(self,
                      host: str, port: int=64738, *,
                      timeout: float=20.0, ignore_tls_cert: bool=False, as_bot: bool=False,
                      version: MumbleVersion | None=None, release_name: str | None=None):
        if version is None:
            version = MumbleVersion(1, 5, 0, 0)
        if release_name is None:
            release_name = "Pumble"

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1
        ssl_context.set_ciphers("AES256-SHA")
        if ignore_tls_cert:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        conn_reader, conn_writer = await asyncio.open_connection(
            host, port, ssl=ssl_context
        )
        self._tcp_connection = MumbleTCPConnection(conn_reader, conn_writer, timeout)

        version_message = Mumble_pb2.Version()
        version_message.version_v2 = version.to_version_int()
        version_message.release = release_name
        version_message.os = platform.system()
        version_message.os_version = platform.release()
        await self._tcp_connection.write_proto(version_message)

        auth_message = Mumble_pb2.Authenticate()
        auth_message.username = self.username
        if self.password is not None:
            auth_message.password = self.password
        if self.tokens is not None:
            auth_message.tokens.extend(self.tokens)
        auth_message.opus = True
        if as_bot:
            auth_message.client_type = 1

        self._connected = True
        self._ticker_task = asyncio.create_task(self._ticker_loop())

    async def _ticker_loop(self):
        while self._connected:
            await asyncio.sleep(5)
            await self._send_ping()

    async def _send_ping(self):
        ping_message = Mumble_pb2.Ping()
        ping_message.timestamp = int(time.time_ns())
        await self._tcp_connection.write_proto(ping_message)
