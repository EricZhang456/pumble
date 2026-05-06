from dataclasses import dataclass
from typing import Optional

from ._proto import Mumble_pb2


@dataclass(eq=False)
class MumbleChannel:
    channel_id: int
    name: str
    linked_channels = list[int]
    position: int
    parent_channel: int
    description: Optional[str] = None
    description_hash: Optional[bytes] = None


    def __eq__(self, other):
        if isinstance(other, MumbleChannel):
            return other.channel_id == self.channel_id
        return False


class MumbleChannelManager:
    def __init__(self):
        self.channels: list[MumbleChannel] = []


    def update_mumble_channel(self, channel_state_msg: Mumble_pb2.ChannelState):
        existing_entry_idx = None
        entry = None
        for index, item in enumerate(self.channels):
            if item.channel_id == channel_state_msg.channel_id:
                existing_entry_idx = index
                entry = item
                break
        if existing_entry_idx is None:
            entry = MumbleChannel(channel_id=channel_state_msg.channel_id,
                                  name=channel_state_msg.name,
                                  position=channel_state_msg.position,
                                  parent_channel=channel_state_msg.parent)
            entry.linked_channels = []
            if channel_state_msg.links:
                entry.linked_channels.extend(channel_state_msg.links)
            if channel_state_msg.description:
                entry.description = channel_state_msg.description
            if channel_state_msg.description_hash:
                entry.description_hash = channel_state_msg.description_hash
            self.channels.append(entry)
        else:
            entry.name = channel_state_msg.name
            if channel_state_msg.description:
                entry.description = channel_state_msg.description
            if channel_state_msg.description_hash:
                entry.description_hash = channel_state_msg.description_hash
            entry.position = channel_state_msg.position
            entry.parent_channel = channel_state_msg.parent
            for i in channel_state_msg.links_add:
                if i not in entry.linked_channels:
                    entry.linked_channels.append(i)
            for k in channel_state_msg.links_remove:
                if k in entry.linked_channels:
                    entry.linked_channels.remove(k)
            self.channels[existing_entry_idx] = entry
        return entry


    def clear_channels(self):
        self.channels = []
