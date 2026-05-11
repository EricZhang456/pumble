from dataclasses import dataclass
from typing import Optional

from .mumble_perm_flags import MumblePerms


@dataclass(eq=False)
class MumbleChannel:
    channel_id: int
    name: str
    linked_channels: list[int]
    position: int
    parent_channel: int
    permissions: MumblePerms = MumblePerms(0)
    description: Optional[str] = None


    def __eq__(self, other):
        if isinstance(other, MumbleChannel):
            return other.channel_id == self.channel_id
        return False
