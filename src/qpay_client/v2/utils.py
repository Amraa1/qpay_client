from logging import Logger
from random import random

from httpx import Response

from .error import QPayError


def safe_json(response: Response) -> dict[str, str]:
    """Avoids json error."""
    try:
        return response.json()
    except ValueError:
        return {"message": response.text}


def handle_error(response: Response, logger: Logger):
    """
    Raise the QPayError a failed response carries.

    QPay puts the machine-readable key in ``error`` (``"INVOICE_PAID"``) and a
    Mongolian text for people in ``message``. ``error_key`` is the key; the
    message stands in only when there is none, as for a body that isn't JSON.
    """
    error_data = safe_json(response)
    logger.error(f"QPayError {response.status_code} error: {error_data}")
    raise QPayError(
        status_code=response.status_code,
        error_key=error_data.get("error") or error_data.get("message", ""),
    )


def exponential_backoff(base_delay: float, attempt: int, jitter: float, max_delay: float = 60.0) -> float:
    """Returns delay for retry backoff."""
    delay = base_delay * (2 ** (attempt - 1)) + random() * jitter
    return min(delay, max_delay)
