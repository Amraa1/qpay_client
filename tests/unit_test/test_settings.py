import importlib

from qpay_client.v2.settings import QPaySettings, SecretStr


def test_default_settings():
    # Client defaults
    username = "TEST_MERCHANT"
    password = "123456"
    sandbox = True
    token_leeway = 60
    client_retries = 5
    client_delay = 0.5
    client_jitter = 0.5
    payment_check_retries = 5
    payment_check_delay = 0.5
    payment_check_jitter = 0.5
    base_url = "https://merchant-sandbox.qpay.mn/v2"

    settings1 = QPaySettings()
    assert settings1.username == username
    assert settings1.password.get_secret_value() == password
    assert settings1.base_url == base_url
    assert settings1.sandbox == sandbox
    assert settings1.token_leeway == token_leeway
    assert settings1.client_retries == client_retries
    assert settings1.client_delay == client_delay
    assert settings1.client_jitter == client_jitter
    assert settings1.payment_check_retries == payment_check_retries
    assert settings1.payment_check_delay == payment_check_delay
    assert settings1.payment_check_jitter == payment_check_jitter


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("QPAY_ENV_FILE", ".env.test")

    # SettingsConfig is run at module import, so for env var to apply we have reload the module
    # import/reload the module that defines Settings
    import qpay_client.v2.settings as settings_mod

    importlib.reload(settings_mod)  # ensures model_config is re-evaluated
    Settings = settings_mod.QPaySettings

    # test env values
    username = "TEST_USER"
    password = "my_secret_password"
    sandbox = False

    settings2 = Settings()
    assert settings2.username == username
    assert settings2.password.get_secret_value() == password
    assert settings2.sandbox == sandbox


def test_settings_with_arguments():
    # Custom settings values
    username = "BLABLA"
    password = "HelloWorld"
    sandbox = False
    base_url = "https://merchant.qpay.mn/v2"
    token_leeway = 123
    client_retries = 9
    client_delay = 0.1
    client_jitter = 0.1
    payment_check_retries = 9
    payment_check_delay = 0.1
    payment_check_jitter = 0.1

    settings = QPaySettings(
        username=username,
        password=SecretStr(password),
        sandbox=sandbox,
        token_leeway=token_leeway,
        client_retries=client_retries,
        client_delay=client_delay,
        client_jitter=client_jitter,
        payment_check_retries=payment_check_retries,
        payment_check_delay=payment_check_delay,
        payment_check_jitter=payment_check_jitter,
    )

    assert settings.username == username
    assert settings.password.get_secret_value() == password
    assert settings.sandbox == sandbox
    assert settings.base_url == base_url
