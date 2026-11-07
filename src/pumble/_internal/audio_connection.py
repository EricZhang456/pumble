from abc import ABC, abstractmethod

from google.protobuf.message import Message

from .._proto import MumbleUDP_pb2 # pylint: disable=no-name-in-module
from .audio_message_type import ProtobufAudioMessageType


class AudioConnection(ABC):
    @abstractmethod
    async def send_audio(self, data: bytes) -> None:
        """Sends an audio message.

        :param data: Audio message
        :type data: bytes
        """


    async def send_protobuf_audio(self, data: Message):
        """Sends a protobuf audio message:

        :param data: Protobuf audio message
        :type data: google.protobuf.message.Message
        """
        match type(data):
            case MumbleUDP_pb2.Audio:
                header = ProtobufAudioMessageType.AUDIO.value.to_bytes(1, byteorder="big")
            case MumbleUDP_pb2.Ping:
                header = ProtobufAudioMessageType.PING.value.to_bytes(1, byteorder="big")
            case _:
                raise ValueError("Not a Mumble UDP Protobuf message.")
        await self.send_audio(header + data.SerializeToString())
