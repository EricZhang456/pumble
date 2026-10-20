from abc import ABC, abstractmethod

from google.protobuf.message import Message

from ..client import MumbleClient


class BaseMessage(ABC):
    """Base message class representing a message that can be sent by the Mumble client."""
    @abstractmethod
    def to_mumble_message(self, client: MumbleClient) -> Message:
        """Convert the message to a Mumble control Protobuf message.

        :param client: MumbleClient instance to convert the message for.
        :type client: MumbleClient
        """
