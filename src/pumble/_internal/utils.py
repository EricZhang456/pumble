from typing import AsyncIterator
from typing import TypeVar


_T = TypeVar("_T")

INT32_MAX = (1 << 31) - 1
UINT64_MAX = (1 << 64) - 1


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
