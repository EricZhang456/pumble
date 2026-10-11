from enum import Enum


class ProtobufAudioMessageType(Enum):
    AUDIO = 0
    PING = 1


class AudioMessageType(Enum):
    CELT_ALPHA = 0
    PING = 1
    SPEEX = 2
    CELT_BETA = 3
    OPUS = 4
