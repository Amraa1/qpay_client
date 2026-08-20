"""
Session-level reporting for the live QPay sandbox tests.

The credentials these tests fall back on are QPay's *public* sandbox merchant,
published in QPay's own documentation. They are deliberately not secrets: the
suite is meant to run on a fresh clone with no setup, and CI needs no secrets
(which also lets it run on pull requests from forks).

The risk is not disclosure, it is silence. If you mean to test against your own
sandbox merchant but mistype the variable name, you would otherwise authenticate
as the shared account and debug the wrong data. So say so, loudly, every time.
"""

import os

PUBLIC_SANDBOX_USERNAME = "TEST_MERCHANT"


def _live_enabled() -> bool:
    return os.environ.get("QPAY_RUN_LIVE_TESTS", "0") == "1"


def pytest_configure(config) -> None:
    """
    Warn when live tests will silently use the shared public sandbox merchant.

    Issued as a config-time warning rather than a report header so that it
    survives the ``-q`` in this project's default addopts.
    """
    if not _live_enabled() or os.environ.get("QPAY_USERNAME"):
        return

    config.issue_config_time_warning(
        UserWarning(
            "QPAY_RUN_LIVE_TESTS=1 but QPAY_USERNAME is unset, so live tests will "
            f"authenticate as {PUBLIC_SANDBOX_USERNAME!r} -- the SHARED public sandbox "
            "merchant. Its data is not yours. Set QPAY_USERNAME/QPAY_PASSWORD "
            "(see .env.example) to use your own sandbox merchant."
        ),
        stacklevel=2,
    )


def pytest_report_header(config) -> str:
    """Announce whether live tests are on, and whose credentials they will use."""
    if not _live_enabled():
        return "qpay sandbox: live tests DISABLED (set QPAY_RUN_LIVE_TESTS=1 to enable)"

    username = os.environ.get("QPAY_USERNAME")
    if username:
        return f"qpay sandbox: live tests ENABLED as {username!r} (from QPAY_USERNAME)"
    return f"qpay sandbox: live tests ENABLED as shared public {PUBLIC_SANDBOX_USERNAME!r}"
