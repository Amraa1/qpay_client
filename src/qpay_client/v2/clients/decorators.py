import asyncio
import time
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


def poll_until_paid(func: SyncMethod) -> SyncMethod:
    """
    Poll the wrapped method until PaymentCheckResponse.count > 0 or retries exhausted.

    Stacks under @auth_required so authentication fires once, then the inner
    function (a single HTTP call) is repeated with exponential backoff.
    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any):
        from ..utils import exponential_backoff

        data = func(self, *args, **kwargs)
        if data.count > 0:
            return data
        for attempt in range(1, self._settings.payment_check_retries + 1):
            self._logger.info(
                "Retrying POST: /payment/check (attempt %d/%d)",
                attempt,
                self._settings.payment_check_retries,
            )
            time.sleep(
                exponential_backoff(
                    self._settings.payment_check_delay,
                    attempt,
                    self._settings.payment_check_jitter,
                )
            )
            data = func(self, *args, **kwargs)
            self._logger.debug("Poll attempt %d: count=%d", attempt, data.count)
            if data.count > 0:
                break
        return data

    return wrapper  # type: ignore[return-value]


def async_poll_until_paid(func: AsyncMethod) -> AsyncMethod:
    """Async version of poll_until_paid."""

    @wraps(func)
    async def wrapper(self, *args: Any, **kwargs: Any):
        from ..utils import exponential_backoff

        data = await func(self, *args, **kwargs)
        if data.count > 0:
            return data
        for attempt in range(1, self._settings.payment_check_retries + 1):
            self._logger.info(
                "Retrying POST: /payment/check (attempt %d/%d)",
                attempt,
                self._settings.payment_check_retries,
            )
            await asyncio.sleep(
                exponential_backoff(
                    self._settings.payment_check_delay,
                    attempt,
                    self._settings.payment_check_jitter,
                )
            )
            data = await func(self, *args, **kwargs)
            self._logger.debug("Poll attempt %d: count=%d", attempt, data.count)
            if data.count > 0:
                break
        return data

    return wrapper  # type: ignore[return-value]
