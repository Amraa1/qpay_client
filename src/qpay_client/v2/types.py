from typing import Annotated

from pydantic import BeforeValidator, HttpUrl, StringConstraints


def validate_url(v: str) -> str:
    return str(HttpUrl(v))


HttpUrlStr = Annotated[str, BeforeValidator(validate_url)]
SubscriptionIntervalType = Annotated[
    str, StringConstraints(min_length=2, max_length=5, pattern=r"^(?:[1-9]\d{0,3})(?:[DWM])$")
]
