class QPayError(Exception):
    """
    Raised when Qpay server returns error
    """

    def __init__(self, *, status_code: int, error_key: str) -> None:
        self.exception_message = f"status_code: {status_code}, error_key: {error_key}"
        super().__init__(self.exception_message)
        self.status_code = status_code
        self.error_key = error_key

    def __repr__(self) -> str:
        return self.exception_message
