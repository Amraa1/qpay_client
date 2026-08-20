"""
Verify an *installed* qpay-client behaves as a consumer expects.

The unit suite imports from the source tree, so it cannot catch packaging
faults: a module missing from the wheel, absent `py.typed`, a stale
`__version__`, or a runtime dependency that was never declared. This script is
the missing check. Run it against a clean environment that has only the built
wheel installed -- never from an editable install, or it proves nothing.

Everything here is copied from README.md. If the README changes, change this.
"""

import importlib.metadata as importlib_metadata
import pathlib
import sys
from decimal import Decimal

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    """Record a named assertion without aborting on the first failure."""
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {label}{f' -- {detail}' if detail else ''}")
    if not condition:
        FAILURES.append(label)


def main() -> int:
    print("qpay-client consumer smoke test")
    print(f"  python {sys.version.split()[0]}")

    # 1. The package imports at all, from a clean environment.
    import qpay_client
    from qpay_client.v2 import AsyncQPayClient, QPayClient, QPayError, QPaySettings
    from qpay_client.v2.enums import ObjectType
    from qpay_client.v2.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest

    # 2. It is genuinely the installed distribution, not a source tree on sys.path.
    location = pathlib.Path(qpay_client.__file__).resolve()
    check("imported from site-packages", "site-packages" in location.parts, str(location))

    # 3. __version__ agrees with the installed distribution metadata.
    dist_version = importlib_metadata.version("qpay-client")
    check(
        "__version__ matches distribution metadata",
        qpay_client.__version__ == dist_version,
        f"__version__={qpay_client.__version__} dist={dist_version}",
    )

    # 4. The package advertises inline types, as the Typing :: Typed classifier claims.
    check("py.typed ships in the wheel", (location.parent / "py.typed").is_file())

    # 5. The README's own example constructs and serializes.
    settings = QPaySettings.sandbox()
    check("QPaySettings.sandbox() targets sandbox", "sandbox" in settings.base_url, settings.base_url)

    invoice = InvoiceCreateSimpleRequest(
        sender_invoice_no="ORDER-1001",
        invoice_receiver_code="terminal",
        invoice_description="Test invoice",
        amount=Decimal("1500"),
        callback_url="https://example.com/qpay/callback?payment_id=ORDER-1001",
    )
    payload = invoice.model_dump(by_alias=True, exclude_none=True, mode="json")
    check("invoice serializes for the API", payload.get("sender_invoice_no") == "ORDER-1001", str(payload))

    # 6. The other documented entry points are importable and wired up.
    check("clients and errors importable", all([AsyncQPayClient, QPayClient, QPayError]))
    check("ObjectType enum usable", ObjectType.invoice.value == "INVOICE")
    check("Offset validates pagination", Offset(page_number=1, page_limit=100).page_limit == 100)
    check(
        "PaymentCheckRequest constructs",
        PaymentCheckRequest(
            object_type=ObjectType.invoice,
            object_id="00000000-0000-0000-0000-000000000000",
            offset=Offset(page_number=1, page_limit=100),
        ).object_type
        is ObjectType.invoice,
    )

    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
