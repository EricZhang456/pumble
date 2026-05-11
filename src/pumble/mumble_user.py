from typing import Optional
from dataclasses import dataclass


@dataclass(eq=False)
class MumbleUser:
    session_id: int
    name: str
    mute: bool
    deaf: bool
    suppress: bool
    self_mute: bool
    self_deaf: bool
    priority_speaker: bool
    recording: bool
    listening_channels: Optional[list[int]] = None
    comment: Optional[str] = None
    cert_hash: Optional[str] = None
    registered_user_id: Optional[int] = None


    def __eq__(self, other):
        if isinstance(other, MumbleUser):
            return other.session_id == self.session_id
        return False
