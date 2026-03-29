from functools import wraps
from typing import Any, Callable, TypeVar

SyncMethod = TypeVar("SyncMethod", bound=Callable[..., Any])
AsyncMethod = TypeVar("AsyncMethod", bound=Callable[..., Any])


def auth_required(func: SyncMethod) -> SyncMethod:
    """Authenticate the sync client before calling an auth-protected method."""

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any):
        self.authenticate()
        return func(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


def async_auth_required(func: AsyncMethod) -> AsyncMethod:
    """Authenticate the async client before calling an auth-protected method."""

    @wraps(func)
    async def wrapper(self, *args: Any, **kwargs: Any):
        await self.authenticate()
        return await func(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]
