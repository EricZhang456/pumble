from dataclasses import dataclass


@dataclass
class MumbleCryptInfo:
    key: bytes
    client_nonce: bytes
    server_nonce: bytes
