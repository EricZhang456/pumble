from .._proto import Mumble_pb2 # pylint: disable=no-name-in-module
from .base_message import BaseMessage


class UserListRequest(BaseMessage):
    def to_mumble_message(self, _):
        return Mumble_pb2.UserList()
