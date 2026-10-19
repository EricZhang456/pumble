from typing import Optional
from dataclasses import dataclass

from .version import MumbleVersionInfo


@dataclass
class ServerInfo:
    version_info: MumbleVersionInfo
    max_bandwidth: Optional[int] = None
    motd: Optional[str] = None
    allow_html: Optional[bool] = None
    max_message_length: Optional[int] = None
    max_image_message_length: Optional[int] = None
    max_users: Optional[int] = None
    recording_allowed: Optional[bool] = None
