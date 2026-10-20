from enum import Enum
from dataclasses import dataclass
from collections.abc import AsyncIterator

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
class BaseAudioFrame:
    position: Position | None
    """Positional data for the audio frame."""
    data: bytes
    """Audio data encoded in PCM."""


@dataclass(frozen=True)
class OutgoingAudioFrame(BaseAudioFrame):
    target: AudioTarget | None


@dataclass(frozen=True)
class IncomingAudioFrame(BaseAudioFrame):
    sender: User | None
    target: AudioTarget | ProtobufAudioTarget
    volume: float | None


AudioStream = AsyncIterator[OutgoingAudioFrame]
