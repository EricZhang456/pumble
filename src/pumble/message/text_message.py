# pylint: disable=protected-access

from typing import Iterable

from .._proto import Mumble_pb2 # pylint: disable=no-name-in-module
from ..user import User
from ..channel import Channel
from .._internal.utils import user_to_session_id, channel_to_channel_id
from .base_message import BaseMessage

class TextMessage(BaseMessage):
    """A text message in a Mumble channel."""
    def __init__(self, text: str, *,
                 channels: Iterable[int | Channel], users: Iterable[int | User],
                 trees: Iterable[int | Channel]):
        self.text = text
        self.channels = list(channels)
        self.users = list(users)
        self.trees = list(trees)


    def to_mumble_message(self, client):
        text_msg = Mumble_pb2.TextMessage()
        text_msg.message = self.text
        for i in self.users:
            text_msg.session.append(user_to_session_id(client._user_manager, i))
        for k in self.channels:
            text_msg.channel_id.append(channel_to_channel_id(client._channel_mamnager, k))
        for j in self.trees:
            text_msg.tree_id.append(channel_to_channel_id(client._channel_mamnager, j))
        return text_msg
