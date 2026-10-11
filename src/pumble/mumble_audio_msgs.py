from enum import Enum
from dataclasses import dataclass

from .mumble_user import MumbleUser

@dataclass(frozen=True)
class Position:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class MumbleAudioTarget:
    id: int


class ProtobufAudioTarget(Enum):
    NORMAL = 0
    SHOUT = 1
    WHISPER = 2
    CHANNEL_LISTENER = 3


@dataclass(frozen=True)
class MumbleAudioPacket:
    sender: MumbleUser
    target: MumbleAudioTarget | ProtobufAudioTarget
    data: bytes
    position: Position | None
    volume: float | None
