import asyncio
import ssl
import datetime
import platform
import inspect
import traceback
from statistics import variance
from collections.abc import Iterable, Callable
from typing import Literal, TypeAlias, List, get_args

from ._proto import Mumble_pb2 # pylint: disable=no-name-in-module
from ._internal.func_utils import get_required_params_for_func
from ._internal.mumble_crypt_info import MumbleCryptInfo
from ._internal.mumble_channel_manager import MumbleChannelManager
from ._internal.mumble_user_manager import MumbleUserManager
from ._internal.mumble_tcp_connection import MumbleTCPConnection
from .mumble_perm_flags import MumblePerms
from .mumble_events import (MumbleReadyEvent, MumbleChannelRemoveEvent, MumbleUserUpdateEvent,
                            MumbleUserRemoveEvent)
from .mumble_packet_type import MumblePacketType
from .mumble_version import MumbleVersion, AbstractMumbleVersion, MumbleVersionInfo
from .mumble_server_info import MumbleServerInfo
from .mumble_channel import MumbleChannel
from .mumble_user import MumbleUser


MumbleEvent: TypeAlias = Literal["ready", "text_message", "channel_update", "channel_remove",
                                 "user_update", "user_remove", "user_connect"]
_VALID_EVENTS = get_args(MumbleEvent)


class MumbleClient:
    def __init__(self,
                 username: str,
                 password: str | None=None,
                 tokens: Iterable[str] | None=None):
        self.username = username
        self.password = password
        self.tokens = tokens
        self._server_info: MumbleServerInfo | None = None
        self._session_id: int | None = None

        self._current_channel_id: int | None = None
        self._tcp_packets_received = 0
        self._connected = False
        self._server_sync_completed = False
        self._ticker_task: asyncio.Task | None = None
        self._read_task: asyncio.Task | None = None
        self._tcp_connection: MumbleTCPConnection | None = None
        self._crypt_info: MumbleCryptInfo | None = None
        self._ping_times: list[int] = []
        self._last_ping_time: datetime.datetime | None = None
        self._listeners: dict[str, list[Callable]] = {}
        self._channel_mamnager = MumbleChannelManager()
        self._user_manager = MumbleUserManager()


    @property
    def channels(self) -> List[MumbleChannel]:
        return self._channel_mamnager.channels


    @property
    def users(self) -> List[MumbleUser]:
        return self._user_manager.users


    @property
    def server_info(self) -> MumbleServerInfo | None:
        return self._server_info


    @property
    def session_id(self) -> int | None:
        return self._session_id


    @property
    def current_channel(self) -> MumbleChannel | None:
        if self._current_channel_id is None:
            return None
        for i in self.channels:
            if i.channel_id == self._current_channel_id:
                return i


    def _clear_server_fields(self):
        self._server_info = None
        self._session_id = None
        self._connected = False
        self._server_sync_completed = False
        self._crypt_info = None
        self._last_ping_time = None
        self._current_channel_id = None
        self._tcp_packets_received = 0
        self._ping_times = []
        self._channel_mamnager.clear_channels()
        self._user_manager.clear_users()


    def run(self,
            host: str, port: int=64738, *,
            timeout: float=60.0, ignore_tls_cert: bool=False, as_bot: bool=False,
            version: AbstractMumbleVersion | None=None, release_name: str | None=None):
        async def loop():
            await self.connect(host, port, timeout=timeout,
                               ignore_tls_cert=ignore_tls_cert, as_bot=as_bot,
                               version=version, release_name=release_name)
        asyncio.run(loop())


    async def connect(self,
                      host: str, port: int=64738, *,
                      timeout: float=20.0, ignore_tls_cert: bool=False, as_bot: bool=False,
                      version: AbstractMumbleVersion | None=None, release_name: str | None=None):
        self._clear_server_fields()

        if version is None:
            version = MumbleVersion(1, 5, 0, 0)
        if release_name is None:
            release_name = "Pumble"

        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1
        ssl_context.set_ciphers("AES256-SHA")
        if ignore_tls_cert:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        conn_reader, conn_writer = await asyncio.open_connection(
            host, port, ssl=ssl_context, ssl_handshake_timeout=timeout
        )
        self._tcp_connection = MumbleTCPConnection(conn_reader, conn_writer)

        version_message = Mumble_pb2.Version()
        if isinstance(version, MumbleVersion):
            version_message.version_v2 = version.to_version_int()
            version_message.version_v1 = version.to_legacy_version().to_version_int()
        else:
            version_message.version_v1 = version.to_version_int()
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
            # event listeners should only have one or zero params for our use case
            func_required_params = get_required_params_for_func(func)
            required_params_count = len(func_required_params)
            if required_params_count > 1:
                raise ValueError(f"Callback function requires more parameters than needed (expected 1 or 0, needs {required_params_count})")
            for param in func_required_params.values():
                if param.kind is param.KEYWORD_ONLY:
                    raise ValueError("Callback function only accepts keyword parameters")
            self._listeners[event_name].append(func)
            return func
        return decorator


    def off(self, event_name: MumbleEvent, callback: Callable):
        if event_name not in _VALID_EVENTS:
            raise ValueError(f"Invalid event name \"{event_name}\".")
        listeners = self._listeners.get(event_name)
        if listeners is None:
            raise ValueError(f"No event listeners have been registered for \"{event_name}\".")
        try:
            self._listeners[event_name].remove(callback)
        except ValueError as exc:
            raise ValueError("Callback has not been registered as an event listener.") from exc


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
            # pylint: disable=bare-except
            except:
                traceback.print_exc()


    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    async def _read_packet_loop(self):
        while self._connected:
            packet_type, packet_bytes = await self._tcp_connection.read_packet()
            self._tcp_packets_received += 1
            # TODO: Fetch description for channels, avatar/comment for users in hash only scenarios
            match packet_type:
                case MumblePacketType.VERSION:
                    server_version_msg = Mumble_pb2.Version()
                    server_version_msg.ParseFromString(packet_bytes)
                    server_version_info = MumbleVersionInfo(
                        version=MumbleVersion.from_version_int(server_version_msg.version_v2),
                        release=server_version_msg.release,
                        os=server_version_msg.os,
                        os_version=server_version_msg.os_version
                    )
                    # other fields come later
                    self._server_info = MumbleServerInfo(version_info=server_version_info)
                case MumblePacketType.CRYPT_SETUP:
                    crypt_setup_msg = Mumble_pb2.CryptSetup()
                    crypt_setup_msg.ParseFromString(packet_bytes)
                    self._crypt_info = MumbleCryptInfo(
                        key=crypt_setup_msg.key,
                        client_nonce=crypt_setup_msg.client_nonce,
                        server_nonce=crypt_setup_msg.server_nonce
                    )
                case MumblePacketType.SERVER_CONFIG:
                    server_config_msg = Mumble_pb2.ServerConfig()
                    server_config_msg.ParseFromString(packet_bytes)
                    if server_config_msg.max_bandwidth:
                        self._server_info.max_bandwidth = server_config_msg.max_bandwidth
                    if server_config_msg.welcome_text:
                        self._server_info.motd = server_config_msg.welcome_text
                    self._server_info.allow_html = server_config_msg.allow_html
                    self._server_info.max_message_length = server_config_msg.message_length
                    self._server_info.max_image_message_length = server_config_msg.message_length
                    self._server_info.max_users = server_config_msg.max_users
                    self._server_info.recording_allowed = server_config_msg.recording_allowed
                    ready_event = MumbleReadyEvent(server_info=self._server_info,
                                                   session_id=self._session_id)
                    await self._emit_event("ready", ready_event)
                case MumblePacketType.PERMISSION_QUERY:
                    perm_query_msg = Mumble_pb2.PermissionQuery()
                    perm_query_msg.ParseFromString(packet_bytes)
                    perms = MumblePerms(perm_query_msg.permissions)
                    self._channel_mamnager.update_perms_for_channel(perm_query_msg.channel_id,
                                                                    perms,
                                                                    perm_query_msg.flush)
                case MumblePacketType.CHANNEL_STATE:
                    channel_state_msg = Mumble_pb2.ChannelState()
                    channel_state_msg.ParseFromString(packet_bytes)
                    channel_entry = self._channel_mamnager.update_mumble_channel(channel_state_msg)
                    if self._server_sync_completed:
                        await self._emit_event("channel_update", channel_entry)
                case MumblePacketType.CHANNEL_REMOVE:
                    channel_remove_msg = Mumble_pb2.ChannelRemove()
                    channel_remove_msg.ParseFromString(packet_bytes)
                    self._channel_mamnager.remove_channel(channel_remove_msg.channel_id)
                    await self._emit_event("channel_remove", MumbleChannelRemoveEvent(channel_remove_msg.channel_id))
                case MumblePacketType.USER_STATE:
                    user_state_msg = Mumble_pb2.UserState()
                    user_state_msg.ParseFromString(packet_bytes)
                    user_entry, new_user_entry = self._user_manager.update_user_info(user_state_msg)
                    if self._server_sync_completed:
                        if new_user_entry:
                            await self._emit_event("user_connect", user_entry)
                        else:
                            await self._emit_event("user_update", MumbleUserUpdateEvent(
                                user=user_entry,
                                actor=user_state_msg.actor
                            ))
                case MumblePacketType.USER_REMOVE:
                    user_remove_msg = Mumble_pb2.UserRemove()
                    user_remove_msg.ParseFromString(packet_bytes)
                    self._user_manager.remove_user(user_remove_msg.session)
                    await self._emit_event("user_remove", MumbleUserRemoveEvent(
                        session_id=user_remove_msg.session,
                        actor=user_remove_msg.actor,
                        ban=user_remove_msg.ban,
                        reason=user_remove_msg.reason
                    ))
                case MumblePacketType.SERVER_SYNC:
                    server_sync_msg = Mumble_pb2.ServerSync()
                    server_sync_msg.ParseFromString(packet_bytes)
                    self._session_id = server_sync_msg.session
                    self._server_info.max_bandwidth = server_sync_msg.max_bandwidth
                    self._server_info.motd = server_sync_msg.welcome_text
                    self._server_sync_completed = True
                    self._current_channel_id = 0
                case MumblePacketType.PING:
                    if self._last_ping_time:
                        ping_time_delta = datetime.datetime.now() - self._last_ping_time
                        ping_time = ping_time_delta / datetime.timedelta(milliseconds=1)
                        self._ping_times.append(ping_time)
                        self._ping_times = self._ping_times[-10:]


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
