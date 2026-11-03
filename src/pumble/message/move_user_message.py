# pylint: disable=protected-access

from .base_message import BaseMessage
from .._proto import Mumble_pb2 # pylint: disable=no-name-in-module
from ..channel import Channel
from ..user import User
from .._internal.utils import channel_to_channel_id, user_to_session_id


class MoveUserMessage(BaseMessage):
    def __init__(self, channel: Channel | int, user: User | int = None):
        self.channel = channel
        self.user = user


    def to_mumble_message(self, client):
        user_state_msg = Mumble_pb2.UserState()
        user_state_msg.channel_id = channel_to_channel_id(client._channel_mamnager, self.channel)
        user_state_msg.actor = client.session_id
        if self.user:
            user_state_msg.session = user_to_session_id(client._user_manager, self.user)
        return user_state_msg
