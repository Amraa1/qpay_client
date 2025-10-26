from enum import Enum


class QPayErrorCode(int, Enum):
    SUCCESS = 200
    VALIDATION_ERROR = 400
    UNAUTHORIZED_ERROR = 401
    FORBIDDEN_ERROR = 403
    UNIQUE_ERROR = 409
    NOT_FOUND_ERROR = 422
    INTERNAL_ERROR = 500


class QPayErrorKey(str, Enum):
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


class QPayError(Exception):
    """Raised when Qpay server returns error."""

    def __init__(self, *, status_code: QPayErrorCode, error_key: QPayErrorKey) -> None:
        self.exception_message = f"status_code: {status_code}, error_key: {error_key}"
        super().__init__(self.exception_message)
        self.status_code = status_code
        self.error_key = error_key

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
