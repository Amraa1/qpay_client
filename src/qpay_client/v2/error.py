from dataclasses import dataclass
from enum import Enum


@dataclass
class QpayErrorDescription:
    """English and Mongolian description of QPay error keys."""

    en: str
    mn: str


class QPayErrorCode(int, Enum):
    """QPay error codes."""

    SUCCESS = 200
    VALIDATION_ERROR = 400
    UNAUTHORIZED_ERROR = 401
    FORBIDDEN_ERROR = 403
    UNIQUE_ERROR = 409
    NOT_FOUND_ERROR = 422
    INTERNAL_ERROR = 500


class QPayErrorKey(str, Enum):
    """QPay error keys."""

    account_bank_duplicated = "ACCOUNT_BANK_DUPLICATED"  # Changed to lowercase
    account_selection_invalid = "ACCOUNT_SELECTION_INVALID"
    authentication_failed = "AUTHENTICATION_FAILED"
    bank_account_notfound = "BANK_ACCOUNT_NOTFOUND"
    bank_mcc_already_added = "BANK_MCC_ALREADY_ADDED"
    bank_mcc_not_found = "BANK_MCC_NOT_FOUND"
    card_terminal_notfound = "CARD_TERMINAL_NOTFOUND"
    client_notfound = "CLIENT_NOTFOUND"
    client_username_duplicated = "CLIENT_USERNAME_DUPLICATED"
    customer_duplicate = "CUSTOMER_DUPLICATE"
    customer_notfound = "CUSTOMER_NOTFOUND"
    customer_register_invalid = "CUSTOMER_REGISTER_INVALID"
    ebarimt_cancel_notsupperded = "EBARIMT_CANCEL_NOTSUPPERDED"
    ebarimt_not_registered = "EBARIMT_NOT_REGISTERED"
    ebarimt_qr_code_invalid = "EBARIMT_QR_CODE_INVALID"
    inform_notfound = "INFORM_NOTFOUND"
    input_code_registered = "INPUT_CODE_REGISTERED"
    input_notfound = "INPUT_NOTFOUND"
    invalid_amount = "INVALID_AMOUNT"
    invalid_object_type = "INVALID_OBJECT_TYPE"
    invoice_already_canceled = "INVOICE_ALREADY_CANCELED"
    invoice_code_invalid = "INVOICE_CODE_INVALID"
    invoice_code_registered = "INVOICE_CODE_REGISTERED"
    invoice_line_required = "INVOICE_LINE_REQUIRED"
    invoice_notfound = "INVOICE_NOTFOUND"
    invoice_paid = "INVOICE_PAID"
    invoice_receiver_data_address_required = "INVOICE_RECEIVER_DATA_ADDRESS_REQUIRED"
    invoice_receiver_data_email_required = "INVOICE_RECEIVER_DATA_EMAIL_REQUIRED"
    invoice_receiver_data_phone_required = "INVOICE_RECEIVER_DATA_PHONE_REQUIRED"
    invoice_receiver_data_required = "INVOICE_RECEIVER_DATA_REQUIRED"
    max_amount_err = "MAX_AMOUNT_ERR"
    mcc_notfound = "MCC_NOTFOUND"
    merchant_already_registered = "MERCHANT_ALREADY_REGISTERED"
    merchant_inactive = "MERCHANT_INACTIVE"
    merchant_notfound = "MERCHANT_NOTFOUND"
    min_amount_err = "MIN_AMOUNT_ERR"
    no_credendials = "NO_CREDENDIALS"
    object_data_error = "OBJECT_DATA_ERROR"
    p2p_terminal_notfound = "P2P_TERMINAL_NOTFOUND"
    payment_already_canceled = "PAYMENT_ALREADY_CANCELED"
    payment_not_paid = "PAYMENT_NOT_PAID"
    payment_notfound = "PAYMENT_NOTFOUND"
    permission_denied = "PERMISSION_DENIED"
    qraccount_inactive = "QRACCOUNT_INACTIVE"
    qraccount_notfound = "QRACCOUNT_NOTFOUND"
    qrcode_notfound = "QRCODE_NOTFOUND"
    qrcode_used = "QRCODE_USED"
    sender_branch_data_required = "SENDER_BRANCH_DATA_REQUIRED"
    tax_line_required = "TAX_LINE_REQUIRED"
    tax_product_code_required = "TAX_PRODUCT_CODE_REQUIRED"
    transaction_not_approved = "TRANSACTION_NOT_APPROVED"
    transaction_required = "TRANSACTION_REQUIRED"


QpayErrorDetail = {
    QPayErrorKey.account_bank_duplicated.value: QpayErrorDescription(
        en="Bank account is already registered!", mn="Банкны данс давхацсан байна"
    ),
    QPayErrorKey.account_selection_invalid.value: QpayErrorDescription(
        en="Account selection is invalid!", mn="Дансны сонголт буруу"
    ),
    QPayErrorKey.authentication_failed.value: QpayErrorDescription(
        en="Your username and password are wrong!", mn="Нэвтрэх нэр нууц үг буруу"
    ),
    QPayErrorKey.bank_account_notfound.value: QpayErrorDescription(
        en="Bank account is not found!", mn="Банкны данс олдсонгүй"
    ),
    QPayErrorKey.bank_mcc_already_added.value: QpayErrorDescription(
        en="Bank MCC is already added!", mn="Банкны MCC кодыг нэмчихсэн байна"
    ),
    QPayErrorKey.bank_mcc_not_found.value: QpayErrorDescription(
        en="Bank MCC is not found!", mn="Банкны MCC код олдсонгүй"
    ),
    QPayErrorKey.card_terminal_notfound.value: QpayErrorDescription(
        en="Card terminal is not registered!", mn="Картын терминал бүртгэлгүй байна"
    ),
    QPayErrorKey.client_notfound.value: QpayErrorDescription(
        en="Client is not registered!", mn="Клиентийн бүртгэл олдсонгүй"
    ),
    QPayErrorKey.client_username_duplicated.value: QpayErrorDescription(
        en="Client username is already exist!", mn="Клиентийн хэрэглэгчийн нэр давхацсан"
    ),
    QPayErrorKey.customer_duplicate.value: QpayErrorDescription(
        en="Customer register duplicated!", mn="Харилцагчийн регистрийн дугаар давхацсан байна!"
    ),
    QPayErrorKey.customer_notfound.value: QpayErrorDescription(
        en="Customer not registered!", mn="Харилцагч бүртгэгдээгүй байна!"
    ),
    QPayErrorKey.customer_register_invalid.value: QpayErrorDescription(
        en="Customer register is wrong!", mn="Харилцагч регистрийн дугаар байна!"
    ),
    QPayErrorKey.ebarimt_cancel_notsupperded.value: QpayErrorDescription(
        en="qPay service eBarimt unregister function not supported",
        mn="qPay үйлчилгээ и-баримтыг цуцлах боломжгүй байна.",
    ),
    QPayErrorKey.ebarimt_not_registered.value: QpayErrorDescription(
        en="eBarimt not registered!", mn="и-Баримт үүсээгүй байна."
    ),
    QPayErrorKey.ebarimt_qr_code_invalid.value: QpayErrorDescription(
        en="eBarimt QR code invalid by merchant", mn="Төлбөр хүлээн авагчийн илгээсэн и-баримт-ын QR код буруу байна."
    ),
    QPayErrorKey.inform_notfound.value: QpayErrorDescription(
        en="Inform is not found!", mn="Мэдэгдэлийн хаяг олдсонгүй"
    ),
    QPayErrorKey.input_code_registered.value: QpayErrorDescription(
        en="Input code is already registered!", mn="Input олдсонгүй"
    ),
    QPayErrorKey.input_notfound.value: QpayErrorDescription(
        en="Input not registered!", mn="Банкны данс давхацсан байна"
    ),
    QPayErrorKey.invalid_amount.value: QpayErrorDescription(en="Amount is invalid!", mn="Үнийн дүн буруу"),
    QPayErrorKey.invalid_object_type.value: QpayErrorDescription(en="Object type is invalid!", mn="object_type буруу"),
    QPayErrorKey.invoice_already_canceled.value: QpayErrorDescription(
        en="Invoice is already cancelled!", mn="Нэхэмжлэл цуцлагдсан байна"
    ),
    QPayErrorKey.invoice_code_invalid.value: QpayErrorDescription(
        en="Invoice code is wrong!", mn="Нэхэмжлэлийн код буруу"
    ),
    QPayErrorKey.invoice_code_registered.value: QpayErrorDescription(
        en="Invoice code is already registered!", mn="Нэхэмжлэлийн код бүртгэгдсэн байна"
    ),
    QPayErrorKey.invoice_line_required.value: QpayErrorDescription(
        en="Invoice line is required!", mn="Нэхэмжлэлийн мөр шаардлагатай"
    ),
    QPayErrorKey.invoice_notfound.value: QpayErrorDescription(en="Invoice is not found!", mn="Нэхэмжлэл олдсонгүй"),
    QPayErrorKey.invoice_paid.value: QpayErrorDescription(en="Invoice is paid!", mn="Нэхэмжлэл төлөгдсөн"),
    QPayErrorKey.invoice_receiver_data_address_required.value: QpayErrorDescription(
        en="Invoice receiver address is required!", mn="Нэхэмжлэл хүлээн авагчийн хаягийн мэдээлэл шаардлагатай"
    ),
    QPayErrorKey.invoice_receiver_data_email_required.value: QpayErrorDescription(
        en="Нэхэмжлэл хүлээн авагчийн имэйл хаяг шаардлагатай", mn="Invoice receiver email is required!"
    ),
    QPayErrorKey.invoice_receiver_data_phone_required.value: QpayErrorDescription(
        en="Invoice receiver phone is required!", mn="Нэхэмжлэл хүлээн авагчийн утасны дугаар шаардлагатай"
    ),
    QPayErrorKey.invoice_receiver_data_required.value: QpayErrorDescription(
        en="Invoice receiver data is required!", mn="Нэхэмжлэл хүлээн авагчийн мэдээлэл шаардлагатай"
    ),
    QPayErrorKey.max_amount_err.value: QpayErrorDescription(
        en="Amount is over than max value!", mn="Үнийн дүн хэт их байна"
    ),
    QPayErrorKey.mcc_notfound.value: QpayErrorDescription(en="MCC is not found!", mn="MCC код олдсонгүй"),
    QPayErrorKey.merchant_already_registered.value: QpayErrorDescription(
        en="Merchant is already registered!", mn="Мерчантын бүртгэл давхацсан"
    ),
    QPayErrorKey.merchant_inactive.value: QpayErrorDescription(en="Merchant is inactive!", mn="Мерчант идэвхигүй"),
    QPayErrorKey.merchant_notfound.value: QpayErrorDescription(
        en="Merchant is not registered!", mn="Мерчант бүртгэлгүй байна"
    ),
    QPayErrorKey.min_amount_err.value: QpayErrorDescription(
        en="Amount is less than minimum value!", mn="Үнийн дүн хэт бага байна"
    ),
    QPayErrorKey.no_credendials.value: QpayErrorDescription(
        en="Your credential is invalid. Please login!", mn="Хандах эрхгүй байна. Нэвтрэнэ үү."
    ),
    QPayErrorKey.object_data_error.value: QpayErrorDescription(en="Object data is wrong!", mn="object_data алдаа"),
    QPayErrorKey.p2p_terminal_notfound.value: QpayErrorDescription(
        en="P2P terminal is not registered!", mn="P2P терминал бүртгэлгүй байна"
    ),
    QPayErrorKey.payment_already_canceled.value: QpayErrorDescription(
        en="Payment is already cancelled!", mn="Төлбөр цуцлагдсан байна"
    ),
    QPayErrorKey.payment_not_paid.value: QpayErrorDescription(
        en="Payment is not paid!", mn="Төлбөр төлөлт хийгдээгүй байна"
    ),
    QPayErrorKey.payment_notfound.value: QpayErrorDescription(en="Payment is not found!", mn="Төлбөр олдсонгүй"),
    QPayErrorKey.permission_denied.value: QpayErrorDescription(
        en="Your access permission is not allowed!", mn="Хандах эрх хүрэхгүй байна"
    ),
    QPayErrorKey.qraccount_inactive.value: QpayErrorDescription(en="QR account is inactive!", mn="QR данс идэвхигүй"),
    QPayErrorKey.qraccount_notfound.value: QpayErrorDescription(en="QR account is not found!", mn="QR данс олдсонгүй"),
    QPayErrorKey.qrcode_notfound.value: QpayErrorDescription(en="QR code is not found!", mn="QR код олдсонгүй"),
    QPayErrorKey.qrcode_used.value: QpayErrorDescription(en="QR code is already used!", mn="QR код ашиглагдаж байна"),
    QPayErrorKey.sender_branch_data_required.value: QpayErrorDescription(
        en="Sender branch data is required!", mn="Илгээгчийн салбарын мэдээлэл шаардлагатай"
    ),
    QPayErrorKey.tax_line_required.value: QpayErrorDescription(
        en="Tax line is required!", mn="Татварын мөр шаардлагатай"
    ),
    QPayErrorKey.tax_product_code_required.value: QpayErrorDescription(
        en="Tax product code is required!", mn="Татварын бүтээгдэхүүний код шаардлагатай"
    ),
    QPayErrorKey.transaction_not_approved.value: QpayErrorDescription(
        en="Transaction line is not approved!", mn="Гүйлгээний мөр зөвшөөрөгдөөгүй байна"
    ),
    QPayErrorKey.transaction_required.value: QpayErrorDescription(
        en="Transaction line is required!", mn="Гүйлгээний мөр шаардлагатай байна"
    ),
}


class QPayError(Exception):
    """Raised when Qpay server returns error."""

    def __init__(self, *, status_code: int, error_key: str) -> None:
        self.status_code = status_code
        self.error_key = error_key
        self.error_detail = QpayErrorDetail.get(self.error_key, "No description.")
        self.exception_message = (
            f"status_code: {self.status_code}, error_key: {self.error_key}, error_description: {self.error_detail}"
        )
        super().__init__(self.exception_message)

    def __repr__(self) -> str:
        return self.exception_message


class ClientConfigError(Exception):
    """Raised when the client is configured wrong."""

    def __init__(self, *attr) -> None:
        self.exception_message = f"incorrect attributes: {attr}"
        super().__init__(self.exception_message)


class AuthError(Exception):
    """Raised when Authentication error has occured."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
