from dataclasses import dataclass


@dataclass
class CryptInfo:
    key: bytes
    client_nonce: bytes
    server_nonce: bytes
