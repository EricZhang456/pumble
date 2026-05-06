import asyncio
import ssl
import datetime
import platform
import inspect
import warnings
from statistics import variance
from collections.abc import Iterable, Callable
from typing import Literal, TypeAlias, get_args

from ._proto import Mumble_pb2
from .mumble_packet_type import MumblePacketType
from .mumble_version import MumbleVersion, MumbleVersionInfo
from .mumble_tcp_connection import MumbleTCPConnection
from .mumble_channel import MumbleChannelManager


MumbleEvent: TypeAlias = Literal["ready", "text_message", "channel_update"]
_VALID_EVENTS = get_args(MumbleEvent)


class MumbleClient:
    def __init__(self,
                 username: str,
                 password: str | None=None,
                 tokens: Iterable[str] | None=None):
        self.username = username
        self.password = password
        self.tokens = tokens
        self.server_version_info: MumbleVersionInfo | None = None

        self._tcp_packets_received = 0
        self._connected = False
        self._server_sync_completed = False
        self._ticker_task: asyncio.Task | None = None
        self._read_task: asyncio.Task | None = None
        self._tcp_connection: MumbleTCPConnection | None = None
        self._ping_times: list[int] = []
        self._last_ping_time: datetime.datetime | None = None
        self._listeners: dict[str, list[Callable]] = {}
        self._channel_mamnager = MumbleChannelManager()


    @property
    def channels(self):
        return self._channel_mamnager.channels


    def _clear_server_fields(self):
        self._connected = False
        self._server_sync_completed = False
        self._last_ping_time = None
        self._tcp_packets_received = 0
        self._ping_times = []
        self._channel_mamnager.clear_channels()


    def run(self,
            host: str, port: int=64738, *,
            timeout: float=20.0, ignore_tls_cert: bool=False, as_bot: bool=False,
            version: MumbleVersion | None=None, release_name: str | None=None):
        asyncio.run(self.connect(host, port, timeout=timeout, ignore_tls_cert=ignore_tls_cert,
                                       as_bot=as_bot, version=version, release_name=release_name))


    async def connect(self,
                      host: str, port: int=64738, *,
                      timeout: float=20.0, ignore_tls_cert: bool=False, as_bot: bool=False,
                      version: MumbleVersion | None=None, release_name: str | None=None):
        self._clear_server_fields()

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
        self._tcp_connection = MumbleTCPConnection(conn_reader, conn_writer)

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
        await self._tcp_connection.write_proto(auth_message)

        self._connected = True
        self._ticker_task = asyncio.create_task(self._ticker_loop())
        self._read_task = asyncio.create_task(self._read_packet_loop())
        await asyncio.gather(self._read_task, self._ticker_task)


    def on(self, event_name: MumbleEvent):
        if event_name not in _VALID_EVENTS:
            raise ValueError(f"Invalid event name \"{event_name}\".")
        def decorator(func):
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(func)
            return func
        return decorator


    async def _emit_event(self, event_name: MumbleEvent, *args, **kwargs):
        listeners = self._listeners.get(event_name)
        if listeners is None:
            return
        for listener in listeners:
            func_sig = inspect.signature(listener)
            try:
                func_sig.bind(*args, **kwargs)
                call_args, call_kwargs = args, kwargs
            except TypeError:
                call_args, call_kwargs = (), {}

            try:
                if inspect.iscoroutinefunction(listener):
                    await listener(*call_args, **call_kwargs)
                else:
                    await asyncio.to_thread(listener, *call_args, **call_kwargs)
            except TypeError:
                # pylint: disable=line-too-long
                warnings.warn(f"Callback function {listener.__name__}() expects more arguments than needed.",
                              RuntimeWarning)


    async def _read_packet_loop(self):
        while self._connected:
            packet_type, packet_bytes = await self._tcp_connection.read_packet()
            self._tcp_packets_received += 1
            match packet_type:
                case MumblePacketType.VERSION:
                    server_message_msg = Mumble_pb2.Version()
                    server_message_msg.ParseFromString(packet_bytes)
                    server_version = MumbleVersion.from_version_int(server_message_msg.version_v2)
                    version_info = MumbleVersionInfo(server_version, server_message_msg.release,
                                                     server_message_msg.os,
                                                     server_message_msg.os_version)
                    self.server_version_info = version_info
                case MumblePacketType.CRYPT_SETUP:
                    crypt_setup_msg = Mumble_pb2.CryptSetup()
                    crypt_setup_msg.ParseFromString(packet_bytes)
                case MumblePacketType.CHANNEL_STATE:
                    channel_state_msg = Mumble_pb2.ChannelState()
                    channel_state_msg.ParseFromString(packet_bytes)
                    channel_entry = self._channel_mamnager.update_mumble_channel(channel_state_msg)
                    if self._server_sync_completed:
                        self._emit_event("channel_update", channel_entry)
                case MumblePacketType.USER_STATE:
                    user_state_msg = Mumble_pb2.UserState()
                    user_state_msg.ParseFromString(packet_bytes)
                case MumblePacketType.SERVER_SYNC:
                    server_sync_msg = Mumble_pb2.ServerSync()
                    server_sync_msg.ParseFromString(packet_bytes)
                    self._server_sync_completed = True
                    await self._emit_event("ready")
                case MumblePacketType.PING:
                    if self._last_ping_time:
                        ping_time_delta = datetime.datetime.now() - self._last_ping_time
                        ping_time = ping_time_delta / datetime.timedelta(milliseconds=1)
                        self._ping_times.append(ping_time)
                        self._ping_times = self._ping_times[-10:]
                        print(self._ping_times)


    async def _ticker_loop(self):
        while self._connected:
            await asyncio.sleep(5)
            await self._send_ping()


    async def _send_ping(self):
        ping_message = Mumble_pb2.Ping()
        ping_message.tcp_packets = self._tcp_packets_received
        if self._ping_times:
            ping_message.tcp_ping_avg = round(sum(self._ping_times) / len(self._ping_times), 2)
            if len(self._ping_times) > 1:
                ping_message.tcp_ping_var = round(variance(self._ping_times), 2)
        now_datetime = datetime.datetime.now()
        ping_message.timestamp = int(now_datetime.timestamp())
        self._last_ping_time = now_datetime
        await self._tcp_connection.write_proto(ping_message)
