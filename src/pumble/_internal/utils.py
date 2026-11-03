from typing import AsyncIterator
from typing import TypeVar

from ..user import User
from ..channel import Channel
from .channel_manager import ChannelManager
from .user_manager import UserManager


_T = TypeVar("_T")

INT32_MAX = (1 << 31) - 1
UINT64_MAX = (1 << 64) - 1
SUPERUSER_ID = 0


async def lookahead_async(iterable: AsyncIterator[_T]) -> AsyncIterator[tuple[_T, bool]]:
    it = aiter(iterable)
    try:
        last = await anext(it)
    except StopAsyncIteration:
        return
    async for val in it:
        yield last, True
        last = val
    yield last, False


def user_to_session_id(user_manager: UserManager, user: User | int):
    if isinstance(user, int):
        if user_manager.find_user_by_session_id(user) is None:
            raise ValueError(f"Invalid session ID {user}")
        return user
    if isinstance(user, User):
        if not user_manager.is_user_available(user):
            raise ValueError(f"Session ID {user.session_id} is not available")
        return user.session_id
    raise ValueError("Invalid user type passed to user_to_session_id")


def channel_to_channel_id(channel_manager: ChannelManager, channel: Channel | int):
    if isinstance(channel, int):
        if channel_manager.find_channel_by_channel_id(channel) is None:
            raise ValueError(f"Invalid channel ID {channel}")
        return channel
    if isinstance(channel, Channel):
        if not channel_manager.is_channel_available(channel):
            raise ValueError(f"Channel ID {channel.channel_id} is not available")
        return channel.channel_id
    raise ValueError("Invalid channel type passed to channel_to_channel_id")
