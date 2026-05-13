import asyncio


class MumbleUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_con_lost: asyncio.Future, voice_connection: MumbleUDPVoiceConnection):
        self.on_con_lost = on_con_lost
        self.voice_connection: MumbleUDPVoiceConnection = voice_connection
        self.transport = None


    def connection_made(self, transport):
        self.transport = transport


    def connection_lost(self, exc):
        pass


    def error_received(self, exc):
        pass


    def datagram_received(self, data, addr):
        pass


class MumbleUDPVoiceConnection:
    def __init__(self, host: str, port: int=64738):
        self.host = host
        self.port = port

        self._lost_packets = 0
        self._good_packets = 0
        self._late_packets = 0
        self._nonce_resyncs = 0
        self._ping_times = []


    def _clear_server_fields(self):
        self._lost_packets = 0
        self._good_packets = 0
        self._late_packets = 0
        self._nonce_resyncs = 0
        self._ping_times = []


    async def connect(self):
        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: MumbleUDPProtocol(on_con_lost, self),
            remote_addr=(self.host, self.port)
        )
