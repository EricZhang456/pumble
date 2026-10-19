from .audio_connection import AudioConnection
from .tcp_connection import TCPConnection
from .packet_type import PacketType


class TCPAudioConnection(AudioConnection):
    def __init__(self, conn: TCPConnection):
        self._conn = conn


    async def send_audio(self, data: bytes):
        await self._conn.write_packet(PacketType.UDP_TUNNEL, data)
