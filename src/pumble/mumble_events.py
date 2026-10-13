import asyncio
from typing import Optional
from dataclasses import dataclass

from .mumble_audio_msgs import AudioPacket
from .mumble_user import User
from .mumble_channel import Channel
from .mumble_server_info import ServerInfo


@dataclass(frozen=True)
class ReadyEvent:
    server_info: ServerInfo
    session_id: int


@dataclass(frozen=True)
class ChannelRemoveEvent:
    channel: Channel


@dataclass(frozen=True)
class UserUpdateEvent:
    user: User
    actor: Optional[int] = None


@dataclass(frozen=True)
class UserRemoveEvent:
    target: User
    actor: User
    ban: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class AudioStreamEvent:
    user: User
    stream: asyncio.Queue[AudioPacket | None]


@dataclass(frozen=True)
class MumbleTextMessageEvent:
    actor: User
    target: list[User] | None
    channels: list[Channel]
    tree: list[Channel] | None
    message: str
