from logging import Logger

from httpx import Response

from .error import QPayError


def safe_json(response: Response) -> dict[str, str]:
    """Avoids json error."""
    try:
        return response.json()
    except Exception:
        return {"message": response.text}


def handle_error(response: Response, logger: Logger):
    """Used for handling qpay server errors."""
    error_data = safe_json(response)
    logger.error(f"QPayError {response.status_code} error: {error_data}")
    raise QPayError(status_code=response.status_code, error_key=error_data.get("message", ""))
