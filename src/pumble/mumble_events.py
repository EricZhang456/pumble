import asyncio
from typing import Optional
from dataclasses import dataclass

from .mumble_audio_msgs import MumbleAudioPacket
from .mumble_user import MumbleUser
from .mumble_channel import MumbleChannel
from .mumble_server_info import MumbleServerInfo


@dataclass(frozen=True)
class MumbleReadyEvent:
    server_info: MumbleServerInfo
    session_id: int


@dataclass(frozen=True)
class MumbleChannelRemoveEvent:
    channel_id: int


@dataclass(frozen=True)
class MumbleUserUpdateEvent:
    user: MumbleUser
    actor: Optional[int] = None


@dataclass(frozen=True)
class MumbleUserRemoveEvent:
    session_id: int
    actor: int
    ban: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class MumbleAudioStreamEvent:
    user: MumbleUser
    stream: asyncio.Queue[MumbleAudioPacket | None]


@dataclass(frozen=True)
class MumbleTextMessageEvent:
    actor: MumbleUser
    target: list[MumbleUser] | None
    channel: MumbleChannel
    tree: list[MumbleChannel] | None
    message: str
