# A lot of this comes from pymumble

import warnings
import struct

from pyogg import OpusDecoder, OpusEncoder # pylint: disable=no-name-in-module
from pyogg.pyogg_error import PyOggError

from .._proto import MumbleUDP_pb2 # pylint: disable=no-name-in-module
from .varint import VarInt
from .mumble_user_manager import MumbleUserManager
from .mumble_audio_message_type import AudioMessageType, ProtobufAudioMessageType
from ..mumble_audio_msgs import ProtobufAudioTarget, Position


class MumbleAudioHandler:
    def __init__(self, user_manager: MumbleUserManager):
        self._decoder = OpusDecoder()
        self._decoder.set_sampling_frequency(48000)
        self._decoder.set_channels(1)
        self._user_manager = user_manager
        self._protobuf_audio = False


    def use_protobuf_audio(self, value: bool):
        self._protobuf_audio = value


    async def read_audio(self, message: bytes):
        if self._protobuf_audio:
            return await self._read_audio_protobuf(message)
        return await self._read_audio_legacy(message)


    async def _read_audio_protobuf(self, message: bytes):
        header = message[0]
        header_type = ProtobufAudioMessageType(header)
        match header_type:
            case ProtobufAudioMessageType.PING:
                return None
            case ProtobufAudioMessageType.AUDIO:
                audio_message = MumbleUDP_pb2.Audio()
                audio_message.ParseFromString(message[1:])
                set_header = audio_message.WhichOneof("Header")
                if set_header == "target":
                    warnings.warn("Received target header from server. This is unexpected.")
                    target = ProtobufAudioTarget.NORMAL
                else:
                    target = ProtobufAudioTarget(audio_message.context)
                session = audio_message.sender_session
                sequence = audio_message.frame_number
                position = None
                if audio_message.positional_data:
                    position = Position(
                        x=audio_message.positional_data[0],
                        y=audio_message.positional_data[1],
                        z=audio_message.positional_data[2]
                    )
                volume = None
                if audio_message.volume_adjustment:
                    volume = audio_message.volume_adjustment
                audio_mut = memoryview(bytearray(audio_message.opus_data))
                try:
                    decoded_audio = bytes(self._decoder.decode(audio_mut))
                except PyOggError:
                    warnings.warn("An error occurred when decoding audio")
                    return None
                return await self._user_manager.put_audio(
                    session_id=session,
                    audio=decoded_audio,
                    sequence=sequence,
                    target=target,
                    position=position,
                    volume=volume
                )


    async def _read_audio_legacy(self, message: bytes):
        pos = 0

        (header,) = struct.unpack("!B", bytes([message[pos]]))

        msg_type = AudioMessageType((header & 0b11100000) >> 5)
        if msg_type == AudioMessageType.PING:
            return None
        # TODO: Handle other audio codecs
        if msg_type in {AudioMessageType.CELT_ALPHA, AudioMessageType.SPEEX, AudioMessageType.CELT_BETA}:
            warnings.warn("Only Opus is currently supported, ignoring audio message")
            return None

        target = header & 0b00011111
        pos += 1

        session = VarInt()
        pos += session.decode(message[pos:pos + 10])

        sequence = VarInt()
        pos += sequence.decode(message[pos:pos + 10])

        # the following comes from pymumble
        terminator = False  # set to true if it's the last 10 ms audio frame for the packet (used with CELT codec)
        while (pos < len(message)) and not terminator:  # get the audio frames one by one
            if msg_type == AudioMessageType.OPUS:
                size = VarInt()  # OPUS use varint for the frame length

                pos += size.decode(message[pos:pos + 10])
                size = size.value

                if not size & 0x2000:  # terminator is 0x2000 in the resulting int.
                    terminator = True  # should actually always be 0 as OPUS can use variable length audio frames

                size &= 0x1fff  # isolate the size from the terminator
            else:
                (header,) = struct.unpack("!B", message[pos:pos + 1])  # CELT length and terminator is encoded in a 1 byte int
                if not header & 0b10000000:
                    terminator = True
                size = header & 0b01111111
                pos += 1

            if size > 0:
                audio_mut = memoryview(bytearray(message[pos:pos + size]))
                try:
                    decoded_audio = bytes(self._decoder.decode(audio_mut))
                except PyOggError:
                    warnings.warn("An error occurred when decoding audio")
                    return None
                # TODO: Handle position
                position = None
                return await self._user_manager.put_audio(
                    session_id=session.value,
                    audio=decoded_audio,
                    sequence=sequence.value,
                    target=target,
                    position=position
                )
