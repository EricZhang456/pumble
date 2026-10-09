from dataclasses import dataclass

from .mumble_user import MumbleUser

@dataclass(frozen=True)
class Position:
    x: float
    y: float
    y: float


@dataclass(frozen=True)
class MumbleAudioTarget:
    id: int


@dataclass(frozen=True)
class MumbleAudioPacket:
    sender: MumbleUser
    target: MumbleAudioTarget
    data: bytes
    position: Position | None
