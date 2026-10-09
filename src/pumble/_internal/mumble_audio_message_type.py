from enum import Enum


class AudioMessageType(Enum):
    CELT_ALPHA = 0
    PING = 1
    SPEEX = 2
    CELT_BETA = 3
    OPUS = 4
