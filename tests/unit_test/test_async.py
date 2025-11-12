import pytest
import respx
from httpx import Response

# Import your client + settings from your package
# Adjust the import path to match your project layout
from qpay_client.v2.client import QPayClient
from qpay_client.v2.enums import EbarimtReceiverType, InvoiceStatus, ObjectType
from qpay_client.v2.schemas import Offset
from qpay_client.v2.settings import QPaySettings, SecretStr


class FakeAuthState:
    """Minimal stand-in for QpayAuthState used inside QPayClient."""

    def __init__(self):
        self._access = "tok_initial"
        self._refresh = "ref_initial"
        self._access_expired = True  # start expired so client authenticates
        self._refresh_expired = False
        self.updated_with = None

    # API used by QPayClient
    def has_access_token(self) -> bool:
        return self._access is not None

    def is_access_expired(self, leeway: float = 0) -> bool:
        return self._access_expired

    def is_refresh_expired(self, leeway: float = 0) -> bool:
        return self._refresh_expired

    def get_access_token(self) -> str:
        return self._access

    def refresh_as_header(self) -> str:
        return f"Bearer {self._refresh}"

    def update(self, token_response):
        # token_response is a pydantic model; we just read fields by name
        # Adjust attribute names if your TokenResponse differs
        self._access = token_response.access_token
        self._refresh = token_response.refresh_token
        self._access_expired = False
        self.updated_with = token_response


@pytest.fixture
def settings():
    # Keep retries small and delays irrelevant for fast tests
    return QPaySettings(
        sandbox=True,
        client_retries=1,
        client_delay=0.0,
        client_jitter=0.0,
        payment_check_retries=1,
        payment_check_delay=0.0,
        payment_check_jitter=0.0,
        username="user",
        password=SecretStr("pass"),  # your settings likely wrap this in a SecretStr
    )


@pytest.fixture
def client(settings, monkeypatch):
    c = QPayClient(settings=settings)

    # Plug in fake auth state so we can control expiry/updates
    fake = FakeAuthState()
    monkeypatch.setattr(c, "_auth_state", fake)

    return c


@pytest.mark.asyncio
@respx.mock
async def test_context_manager_triggers_auth_and_closes(client, settings):
    # Mock /auth/token for first-time auth
    respx.post(f"{settings.base_url}/auth/token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_AAA",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    respx.post(f"{settings.base_url}/auth/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_AAA",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    async with client as c:
        assert c.is_authenticated is True
        assert c.token == "tok_AAA"

    # After exiting the context, the underlying httpx.AsyncClient should be closed
    assert client.is_closed is True


@pytest.mark.asyncio
@respx.mock
async def test_headers_include_bearer_token_after_auth(client, settings):
    # First authenticate
    respx.post(f"{settings.base_url}/auth/token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_HDR",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    respx.post(f"{settings.base_url}/auth/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_HDR",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    # Then call any endpoint and inspect the Authorization header on the request
    route = respx.get(f"{settings.base_url}/invoice/INV123").mock(
        return_value=Response(
            200,
            json={
                "invoice_id": "INV123",
                "invoice_status": InvoiceStatus.open,
                "sender_invoice_no": "123456",
                "invoice_description": "Cool invoice",
                "total_amount": "123",
                "gross_amount": "123",
                "tax_amount": "123",
                "surcharge_amount": "122",
                "callback_url": "https://www.example.com/callback",
                "note": "123",
                "lines": [],
                "transactions": [],
                "inputs": [],
            },
        )
    )

    await client.invoice_get("INV123")

    assert route.called
    # Check last request headers; respx keeps them on the call
    auth = route.calls.last.request.headers.get("Authorization")
    assert auth == "Bearer tok_HDR"


@pytest.mark.asyncio
@respx.mock
async def test_request_retries_on_500_then_succeeds(client, settings):
    # Authenticate first
    respx.post(f"{settings.base_url}/auth/token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_AAA",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    respx.post(f"{settings.base_url}/auth/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_HDR",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    # First call returns 500, second returns 200 — client should retry
    route = respx.get(f"{settings.base_url}/payment/PAY123").mock(
        side_effect=[
            Response(500, json={"detail": "server error"}),
            Response(
                200,
                json={
                    "payment_id": "PAY123",
                    "payment_status": "PAID",
                    "payment_fee": "0.00",
                    "payment_amount": "120.00",
                    "payment_currency": "MNT",
                    "payment_date": "2025-03-10T07:45:20.214Z",
                    "payment_wallet": "0fc9b71c-cd87-4ffd-9cac-2279ebd9deb0",
                    "object_type": "INVOICE",
                    "object_id": "893e1017-f8b5-4bf3-9178-010f847dceee",
                    "next_payment_date": None,
                    "next_payment_datetime": None,
                    "transaction_type": "P2P",
                    "card_transactions": [],
                    "p2p_transactions": [
                        {
                            "id": "162640477368519",
                            "transaction_bank_code": "050000",
                            "account_bank_code": "340000",
                            "account_bank_name": "Хаан банк",
                            "account_number": "102200004144",
                            "status": "SUCCESS",
                            "amount": "118.80",
                            "currency": "MNT",
                            "settlement_status": "SETTLED",
                        }
                    ],
                },
            ),
        ]
    )

    data = await client.payment_get("PAY123")
    assert route.called
    assert route.call_count == 2
    assert data.payment_id == "PAY123"


@pytest.mark.asyncio
@respx.mock
async def test_401_triggers_refresh_and_replays_request(client, settings, monkeypatch):
    # Start with non-expired access token so client won't call /auth/token first
    client._auth_state._access_expired = False

    # Original request returns 401, then after refresh it returns 200
    route = respx.get(f"{settings.base_url}/invoice/a0b9f668-8a83-41e5-bbaf-3109e6aac600").mock(
        side_effect=[
            Response(401, json={"detail": "expired"}),
            Response(
                200,
                json={
                    "invoice_id": "a0b9f668-8a83-41e5-bbaf-3109e6aac600",
                    "invoice_status": "OPEN",
                    "sender_invoice_no": "123456",
                    "sender_branch_code": "Your mom",
                    "sender_branch_data": None,
                    "sender_staff_code": None,
                    "sender_staff_data": None,
                    "sender_terminal_code": None,
                    "sender_terminal_data": None,
                    "invoice_description": "aaaaaaaaaaaaaaaaaaaaa",
                    "invoice_due_date": None,
                    "enable_expiry": True,
                    "expiry_date": "2025-10-29T07:48:01.724Z",
                    "allow_partial": False,
                    "minimum_amount": None,
                    "allow_exceed": False,
                    "maximum_amount": None,
                    "total_amount": "220.00",
                    "gross_amount": 200,
                    "tax_amount": 20,
                    "surcharge_amount": 10,
                    "discount_amount": 10,
                    "callback_url": "https://bd5492c3ee85.ngrok.io/payments?payment_id=12345678",
                    "note": None,
                    "lines": [
                        {
                            "tax_product_code": "6401",
                            "line_description": " Order No1311 200.00 .",
                            "line_quantity": "1.00",
                            "line_unit_price": "200.00",
                            "note": "-.",
                            "discounts": [
                                {
                                    "discount_code": "NONE",
                                    "description": " discounts",
                                    "amount": "10.00",
                                    "note": " discounts",
                                }
                            ],
                            "surcharges": [
                                {
                                    "surcharge_code": "NONE",
                                    "description": "Хүргэлтийн зардал",
                                    "amount": "10.00",
                                    "note": " Хүргэлт",
                                }
                            ],
                            "taxes": [{"tax_code": "VAT", "description": "НӨАТ", "amount": "20.0000", "note": " НӨАТ"}],
                        }
                    ],
                    "transactions": [],
                    "inputs": [],
                },
            ),
        ]
    )

    # Refresh endpoint returns a new token
    respx.post(f"{settings.base_url}/auth/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_NEW",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    data = await client.invoice_get("a0b9f668-8a83-41e5-bbaf-3109e6aac600")
    assert route.call_count == 2
    assert client.token == "tok_initial"
    assert data.invoice_id == "a0b9f668-8a83-41e5-bbaf-3109e6aac600"


@pytest.mark.asyncio
@respx.mock
async def test_payment_check_polls_until_count_gt_zero(client, settings):
    # Authenticate first
    respx.post(f"{settings.base_url}/auth/token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_POLL",
                "refresh_token": "ref_POLL",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
            },
        )
    )

    respx.post(f"{settings.base_url}/auth/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_NEW",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    # First response: count = 0, Second response: count = 1 (success)
    route = respx.post(f"{settings.base_url}/payment/check").mock(
        side_effect=[
            Response(200, json={"count": 0, "rows": []}),
            Response(
                200,
                json={
                    "count": 1,
                    "paid_amount": 198081,
                    "rows": [
                        {
                            "payment_id": "912213777662363",
                            "payment_status": "PAID",
                            "payment_amount": "198081.00",
                            "trx_fee": "1980.81",
                            "payment_currency": "MNT",
                            "payment_wallet": "Хаан банк апп",
                            "payment_type": "P2P",
                            "next_payment_date": None,
                            "next_payment_datetime": None,
                            "card_transactions": [],
                            "p2p_transactions": [
                                {
                                    "id": "084064367153900",
                                    "transaction_bank_code": "050000",
                                    "account_bank_code": "340000",
                                    "account_bank_name": "Төрийн банк",
                                    "account_number": "MN160034102200004144",
                                    "status": "SUCCESS",
                                    "amount": "196100.19",
                                    "currency": "MNT",
                                    "settlement_status": "SETTLED",
                                }
                            ],
                        }
                    ],
                },
            ),
        ]
    )

    from qpay_client.v2.schemas import PaymentCheckRequest  # adjust import

    req = PaymentCheckRequest(
        object_type=ObjectType.invoice, object_id="912213777662363", offset=Offset(page_limit=100, page_number=1)
    )
    res = await client.payment_check(req)

    assert route.call_count == 2
    assert res.count == 1
    assert res.rows[0].payment_id == "912213777662363"


@pytest.mark.asyncio
@respx.mock
async def test_ebarimt_create_parses_response(client, settings):
    # Authenticate first
    respx.post(f"{settings.base_url}/auth/token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_EB",
                "refresh_token": "ref_EB",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
            },
        )
    )

    respx.post(f"{settings.base_url}/auth/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "tok_NEW",
                "refresh_token": "ref_AAA",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "token_type": "Bearer",
                "scope": "session",
                "not-before-policy": "1",
                "session_state": "1",
            },
        )
    )

    respx.post(f"{settings.base_url}/ebarimt/create").mock(
        return_value=Response(
            200,
            json={
                "id": "b5e2a8fa-dc71-42e4-95de-7d57a39a5b3e",
                "ebarimt_by": "merchant_system",
                "g_wallet_id": "fa9d3b40-77d4-44a8-9e5f-2f7d84cc3cc7",
                "g_wallet_customer_id": "77ffb9cd-9c8d-44cc-9834-06f7f8b7d621",
                "ebarim_receiver_type": "CITIZEN",
                "ebarimt_receiver": "99119922",
                "ebarimt_district_code": "1201",
                "ebarimt_bill_type": "BILL_TYPE_1",
                "g_merchant_id": "d42acb64-f1da-4e73-a780-6a9389d890b2",
                "merchant_branch_code": "001",
                "merchant_terminal_code": "POS-01",
                "merchant_staff_code": "STF-1234",
                "merchant_register": "1234567",
                "g_payment_id": "987654321",
                "paid_by": "CARD",
                "object_type": "INVOICE",
                "object_id": "2f7c9b2a-d9b0-4f9f-93ea-4512a8c4e3a7",
                "amount": "120000.00",
                "vat_amount": "12000.00",
                "city_tax_amount": "3000.00",
                "ebarimt_qr_data": "https://ebarimt.mn/qr?data=example",
                "ebarimt_lottery": "A1B2C3D4",
                "note": "Payment completed successfully.",
                "ebarimt_status": "SUCCESS",
                "ebarimt_status_date": "2025-11-12T10:00:00Z",
                "tax_type": "VAT",
                "created_by": "system",
                "created_date": "2025-11-12T09:58:00Z",
                "updated_by": "system",
                "updated_date": "2025-11-12T10:00:00Z",
                "status": True,
            },
        )
    )

    from qpay_client.v2.schemas import EbarimtCreateRequest  # adjust import

    req = EbarimtCreateRequest(
        payment_id="1234",
        ebarimt_receiver_type=EbarimtReceiverType.citizen,
    )
    eb = await client.ebarimt_create(req)

    assert eb.id == "b5e2a8fa-dc71-42e4-95de-7d57a39a5b3e"
