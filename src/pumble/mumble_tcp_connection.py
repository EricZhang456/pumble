import asyncio
import struct

from google.protobuf.message import Message

from .mumble_packet_type import MumblePacketType, get_mumble_packet_type_from_proto


class MumbleTCPConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer


    async def read_packet(self) -> tuple[MumblePacketType, bytes]:
        header = await self.reader.readexactly(6)
        packet_type, packet_len = struct.unpack(">HI", header)
        if packet_type != 1:
            print(packet_type)
        data = await self.reader.readexactly(packet_len)
        return MumblePacketType(packet_type), data


    async def write_packet(self, packet_type: MumblePacketType, data: bytes):
        self.writer.write(self._make_header(packet_type, len(data)))
        self.writer.write(data)
        await self.writer.drain()


    async def write_proto(self, message: Message):
        data = message.SerializeToString()
        packet_type = get_mumble_packet_type_from_proto(message)
        await self.write_packet(packet_type, data)


    def _make_header(self, packet_type: MumblePacketType, length: int) -> bytes:
        type_uint16 = packet_type.value.to_bytes(2, "big")
        length_uint32 = length.to_bytes(4, "big")
        return type_uint16 + length_uint32
