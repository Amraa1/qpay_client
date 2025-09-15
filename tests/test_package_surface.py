def test_v2_exports_and_help_sanity():
    # Ensure v2 exposes both clients (mirrors your v2 __init__.py)
    import qpay_client.v2 as v2

    assert hasattr(v2, "QPayClient")
    assert hasattr(v2, "QPayClientSync")

    # Light sanity: importing top-level should not explode
    import qpay_client as pkg  # noqa
