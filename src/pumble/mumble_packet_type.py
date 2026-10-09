"""Mumble packet type enum."""
from enum import Enum

from google.protobuf.message import Message

from ._proto import Mumble_pb2 # pylint: disable=no-name-in-module


class MumblePacketType(Enum):
    """Types of Mumble packets."""
    VERSION = 0
    UDP_TUNNEL = 1
    AUTHENTICATE = 2
    PING = 3
    REJECT = 4
    SERVER_SYNC = 5
    CHANNEL_REMOVE = 6
    CHANNEL_STATE = 7
    USER_REMOVE = 8
    USER_STATE = 9
    BAN_LIST = 10
    TEXT_MESSAGE = 11
    PERMISSION_DENIED = 12
    ACL = 13
    QUERY_USERS = 14
    CRYPT_SETUP = 15
    CONTEXT_ACTION_MODIFY = 16
    CONTEXT_ACTION = 17
    USER_LIST = 18
    VOICE_TARGET = 19
    PERMISSION_QUERY = 20
    CODEC_VERSION = 21
    USER_STATS = 22
    REQUEST_BLOB = 23
    SERVER_CONFIG = 24
    SUGGEST_CONFIG = 25


def get_mumble_packet_type_from_proto(message: Message) -> MumblePacketType:
    """Gets the Mumble packet type from a Mumble Protobuf message.

    :param message: The Protobuf message.
    :raises ValueError: Message is not a Mumble Protobuf message.
    :return: The Mumble packet type.
    :rtype: MumblePacketType
    """
    match type(message):
        case Mumble_pb2.Version:
            return MumblePacketType.VERSION
        case Mumble_pb2.UDPTunnel:
            return MumblePacketType.UDP_TUNNEL
        case Mumble_pb2.Authenticate:
            return MumblePacketType.AUTHENTICATE
        case Mumble_pb2.Ping:
            return MumblePacketType.PING
        case Mumble_pb2.Reject:
            return MumblePacketType.REJECT
        case Mumble_pb2.ServerSync:
            return MumblePacketType.SERVER_SYNC
        case Mumble_pb2.ChannelRemove:
            return MumblePacketType.CHANNEL_REMOVE
        case Mumble_pb2.ChannelState:
            return MumblePacketType.CHANNEL_STATE
        case Mumble_pb2.UserRemove:
            return MumblePacketType.USER_REMOVE
        case Mumble_pb2.UserState:
            return MumblePacketType.USER_STATE
        case Mumble_pb2.BanList:
            return MumblePacketType.BAN_LIST
        case Mumble_pb2.TextMessage:
            return MumblePacketType.TEXT_MESSAGE
        case Mumble_pb2.PermissionDenied:
            return MumblePacketType.PERMISSION_DENIED
        case Mumble_pb2.ACL:
            return MumblePacketType.ACL
        case Mumble_pb2.QueryUsers:
            return MumblePacketType.QUERY_USERS
        case Mumble_pb2.CryptSetup:
            return MumblePacketType.CRYPT_SETUP
        case Mumble_pb2.ContextActionModify:
            return MumblePacketType.CONTEXT_ACTION_MODIFY
        case Mumble_pb2.ContextAction:
            return MumblePacketType.CONTEXT_ACTION
        case Mumble_pb2.UserList:
            return MumblePacketType.USER_LIST
        case Mumble_pb2.VoiceTarget:
            return MumblePacketType.VOICE_TARGET
        case Mumble_pb2.PermissionQuery:
            return MumblePacketType.PERMISSION_QUERY
        case Mumble_pb2.CodecVersion:
            return MumblePacketType.CODEC_VERSION
        case Mumble_pb2.UserStats:
            return MumblePacketType.USER_STATS
        case Mumble_pb2.RequestBlob:
            return MumblePacketType.REQUEST_BLOB
        case Mumble_pb2.ServerConfig:
            return MumblePacketType.SERVER_CONFIG
        case Mumble_pb2.SuggestConfig:
            return MumblePacketType.SUGGEST_CONFIG
        case _:
            raise ValueError("Not a Mumble Protobuf message.")
