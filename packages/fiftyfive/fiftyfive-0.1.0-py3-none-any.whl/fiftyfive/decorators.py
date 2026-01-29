from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Awaitable, Callable, cast

if TYPE_CHECKING:
    from .api import Api


def authenticated[**P, T](func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Authenticate when a call returns an empty list"""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        self = cast("Api", args[0])

        if not [c for c in self.session.cookie_jar if c.key == "PHPSESSID"]:
            await self.login()

        return await func(*args, **kwargs)

    return wrapper
