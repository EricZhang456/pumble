from enum import Enum
from dataclasses import dataclass

from .user import User

@dataclass(frozen=True)
class Position:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class AudioTarget:
    id: int


class ProtobufAudioTarget(Enum):
    NORMAL = 0
    SHOUT = 1
    WHISPER = 2
    CHANNEL_LISTENER = 3


@dataclass(frozen=True)
class AudioPacket:
    sender: User
    target: AudioTarget | ProtobufAudioTarget
    data: bytes
    position: Position | None
    volume: float | None
