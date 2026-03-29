from qpay_client.v2.defaults import MERCHANT_URL, SANDBOX_INVOICE_CODE, SANDBOX_PASSWORD, SANDBOX_URL, SANDBOX_USERNAME
from qpay_client.v2.settings import QPaySettings


def test_sandbox_settings_use_expected_defaults():
    settings = QPaySettings.sandbox()

    assert settings.username == SANDBOX_USERNAME
    assert settings.password == SANDBOX_PASSWORD
    assert settings.invoice_code == SANDBOX_INVOICE_CODE
    assert settings.base_url == SANDBOX_URL
    assert settings.token_leeway == 60.0
    assert settings.client_retries == 5
    assert settings.client_delay == 0.5
    assert settings.client_jitter == 0.5
    assert settings.payment_check_retries == 5
    assert settings.payment_check_delay == 0.5
    assert settings.payment_check_jitter == 0.5


def test_sandbox_settings_allow_overrides():
    settings = QPaySettings.sandbox(
        username="override-user",
        password="override-password",
        invoice_code="OVERRIDE-INVOICE",
        client_retries=1,
        payment_check_retries=2,
    )

    assert settings.username == "override-user"
    assert settings.password == "override-password"
    assert settings.invoice_code == "OVERRIDE-INVOICE"
    assert settings.base_url == SANDBOX_URL
    assert settings.client_retries == 1
    assert settings.payment_check_retries == 2


def test_production_settings_use_merchant_url_and_custom_values():
    settings = QPaySettings.production(
        username="merchant-user",
        password="merchant-password",
        invoice_code="INV-123",
        token_leeway=123.0,
        client_retries=9,
        client_delay=0.1,
        client_jitter=0.2,
        payment_check_retries=3,
        payment_check_delay=0.4,
        payment_check_jitter=0.1,
    )

    assert settings.username == "merchant-user"
    assert settings.password == "merchant-password"
    assert settings.invoice_code == "INV-123"
    assert settings.base_url == MERCHANT_URL
    assert settings.token_leeway == 123.0
    assert settings.client_retries == 9
    assert settings.client_delay == 0.1
    assert settings.client_jitter == 0.2
    assert settings.payment_check_retries == 3
    assert settings.payment_check_delay == 0.4
    assert settings.payment_check_jitter == 0.1
