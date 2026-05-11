from .._proto import Mumble_pb2 # pylint: disable=no-name-in-module
from ..mumble_perm_flags import MumblePerms
from ..mumble_channel import MumbleChannel


class MumbleChannelManager:
    def __init__(self):
        self._channels: list[MumbleChannel] = []


    @property
    def channels(self):
        return self._channels


    def update_mumble_channel(self, channel_state_msg: Mumble_pb2.ChannelState) -> MumbleChannel:
        existing_entry_idx = None
        entry = None
        for index, item in enumerate(self._channels):
            if item.channel_id == channel_state_msg.channel_id:
                existing_entry_idx = index
                entry = item
                break
        if existing_entry_idx is None:
            entry = MumbleChannel(channel_id=channel_state_msg.channel_id,
                                  name=channel_state_msg.name,
                                  position=channel_state_msg.position,
                                  parent_channel=channel_state_msg.parent,
                                  linked_channels=[])
            if channel_state_msg.links:
                entry.linked_channels.extend(channel_state_msg.links)
            if channel_state_msg.description:
                entry.description = channel_state_msg.description
            if channel_state_msg.description_hash:
                entry.description_hash = channel_state_msg.description_hash
            self._channels.append(entry)
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
            self._channels[existing_entry_idx] = entry
        return entry


    def update_perms_for_channel(self, channel_id: int, perms: MumblePerms, flush: bool):
        for index, item in enumerate(self._channels):
            if item.channel_id == channel_id:
                curr_channel = item
                if flush:
                    curr_channel.permissions = perms
                else:
                    curr_channel.permissions |= perms
                self._channels[index] = curr_channel
                break


    def remove_channel(self, channel_id: int):
        for index, item in enumerate(self._channels):
            if item.channel_id == channel_id:
                self._channels.pop(index)
                break


    def clear_channels(self):
        self._channels = []
