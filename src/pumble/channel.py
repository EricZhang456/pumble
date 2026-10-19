from dataclasses import dataclass
from typing import Optional

from .perm_flags import Permission


@dataclass(eq=False)
class Channel:
    channel_id: int
    name: str
    linked_channels: list[int]
    position: int
    parent_channel: int
    permissions: Permission = Permission(0)
    description: Optional[str] = None


    def __eq__(self, other):
        if isinstance(other, Channel):
            return other.channel_id == self.channel_id
        return False
