# A lot of this comes from pymumble

import asyncio
import struct

from opuslib import Decoder, Encoder
from opuslib.exceptions import OpusError

from .logger import logger
from .._proto import MumbleUDP_pb2 # pylint: disable=no-name-in-module
from .varint import VarInt
from .user_manager import UserManager
from .audio_message_type import AudioMessageType, ProtobufAudioMessageType
from ..audio_msgs import ProtobufAudioTarget, Position, AudioStream
from .audio_connection import AudioConnection
from .utils import UINT64_MAX, INT32_MAX, lookahead_async


_AUDIO_FRAME_SIZE = 4096
_AUDIO_SAMPLING_RATE = 48000
_AUDIO_CHANNELS = 1


class AudioHandler:
    def __init__(self, user_manager: UserManager):
        self._decoder = Decoder(fs=_AUDIO_SAMPLING_RATE, channels=_AUDIO_CHANNELS)
        self._encoder = Encoder(fs=_AUDIO_SAMPLING_RATE, channels=_AUDIO_CHANNELS, application="voip")
        self._user_manager = user_manager
        self._audio_lock = asyncio.Lock()
        self._protobuf_audio = False
        self._audio_connection = None


    def use_protobuf_audio(self, value: bool):
        self._protobuf_audio = value


    def set_audio_connection(self, conn: AudioConnection):
        self._audio_connection = conn


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
                    logger.error("Received target header from server. This is unexpected.")
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
                try:
                    decoded_audio = self._decoder.decode(audio_message.opus_data, _AUDIO_FRAME_SIZE)
                except OpusError:
                    logger.error("An error occurred when decoding audio")
                    return None
                ret = await self._user_manager.put_audio(
                    session_id=session,
                    audio=decoded_audio,
                    sequence=sequence,
                    target=target,
                    position=position,
                    volume=volume
                )
                is_terminator = audio_message.is_terminator
                if is_terminator:
                    await self._user_manager.end_audio(session_id=session, sequence=sequence)
                return *ret, is_terminator


    async def _read_audio_legacy(self, message: bytes):
        pos = 0

        (header,) = struct.unpack("!B", bytes([message[pos]]))

        msg_type = AudioMessageType((header & 0b11100000) >> 5)
        if msg_type == AudioMessageType.PING:
            return None
        # TODO: Handle other audio codecs
        if msg_type in {AudioMessageType.CELT_ALPHA, AudioMessageType.SPEEX, AudioMessageType.CELT_BETA}:
            logger.warning("Only Opus is currently supported, ignoring audio message")
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
                try:
                    decoded_audio = self._decoder.decode(message[pos:pos + size], _AUDIO_FRAME_SIZE)
                except OpusError:
                    logger.error("An error occurred when decoding audio")
                    return None
                # TODO: Handle position
                position = None
                ret = await self._user_manager.put_audio(
                    session_id=session.value,
                    audio=decoded_audio,
                    sequence=sequence.value,
                    target=target,
                    position=position
                )
                if terminator:
                    await self._user_manager.end_audio(session_id=session, sequence=sequence.value)
                return *ret, terminator


    async def send_audio(self, stream: AudioStream):
        if self._audio_connection is None:
            raise RuntimeError("send_audio called when AudioConnection has not been registered")
        if self._protobuf_audio:
            await self._send_audio_protobuf(stream)
        else:
            await self._send_audio_legacy(stream)


    async def _send_audio_protobuf(self, stream: AudioStream):
        async with self._audio_lock:
            sequence = 0
            async for item, has_next in lookahead_async(stream):
                audio_msg = MumbleUDP_pb2.Audio()
                audio_msg.frame_number = sequence
                audio_msg.is_terminator = not has_next
                audio_msg.opus_data = self._encoder.encode(item.data, len(item.data) // _AUDIO_CHANNELS)
                if item.target is not None:
                    target_id = item.target.id
                    if target_id > 30 or target_id in {0, 1}:
                        logger.error("Outgoing audio frame has an invalid target id, ignoring. Target ID: %d", target_id)
                        audio_msg.target = 0
                    else:
                        audio_msg.target = target_id
                else:
                    audio_msg.target = 0
                if item.position is not None:
                    audio_msg.positional_data.extend((item.position.x, item.position.y, item.position.z))
                sequence = (sequence + 1) % UINT64_MAX
                await self._audio_connection.send_protobuf_audio(audio_msg)


    async def _send_audio_legacy(self, stream: AudioStream):
        async with self._audio_lock:
            sequence = 0
            async for item, has_next in lookahead_async(stream):
                target_id = 0
                if item.target is not None:
                    msg_target_id = item.target.id
                    if msg_target_id > 30 or msg_target_id in {0, 1}:
                        logger.error("Outgoing audio frame has an invalid target id, ignoring. Target ID: %d", msg_target_id)
                    else:
                        target_id = msg_target_id
                header = struct.pack("!B", AudioMessageType.OPUS.value << 5 | target_id)
                audio_data = self._encoder.encode(item.data, len(item.data) // _AUDIO_CHANNELS)
                length = len(audio_data)
                if not has_next:
                    length |= 0x2000
                length_varint = VarInt(length).encode()
                payload = header + length_varint + audio_data
                if item.position is not None:
                    payload += struct.pack("fff", item.position.x, item.position.y, item.position.z)
                await self._audio_connection.send_audio(payload)
                sequence = (sequence + 1) % INT32_MAX
