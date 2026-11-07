from abc import ABC, abstractmethod

from google.protobuf.message import Message

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
        await self.send_audio(ProtobufAudioMessageType.AUDIO.value.to_bytes(1, byteorder="big") + data.SerializeToString())
