from enum import IntFlag


# https://github.com/mumble-voip/mumble/blob/ea64b1246f3f020172fa9fbcda94f2c8ed0810de/src/ACL.h#L21-L46
class Permission(IntFlag):
    NONE = 0x0
    WRITE = 0x1
    TRAVERSE = 0x2
    ENTER = 0x4
    SPEAK = 0x8
    MUTE_DEAFEN = 0x10
    MOVE = 0x20
    MAKE_CHANNEL = 0x40
    LINK_CHANNEL = 0x80
    WHISPER = 0x100
    TEXT_MESSAGE = 0x200
    MAKE_TEMP_CHANNEL = 0x400
    LISTEN = 0x800

    KICK = 0x10000
    BAN = 0x20000
    REGISTER = 0x40000
    SELF_REGISTER = 0x80000
    RESET_USER_CONTENT = 0x100000

    CACHED = 0x8000000
