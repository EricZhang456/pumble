import asyncio
from typing import Optional
from dataclasses import dataclass

from .perm_flags import DenyType, Permission
from .audio_msgs import IncomingAudioFrame
from .user import User
from .channel import Channel
from .server_info import ServerInfo


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
    stream: asyncio.Queue[IncomingAudioFrame | None]


@dataclass(frozen=True)
class TextMessageEvent:
    actor: User
    target: list[User] | None
    channels: list[Channel]
    tree: list[Channel] | None
    message: str


@dataclass(frozen=True)
class PermissionDeniedEvent:
    permission: Permission | None
    channel: Channel | None
    user: User
    reason: str
    deny_type: DenyType
    name: str | None
