from typing import Dict, Optional


class ArzekaPaymentError(Exception):
    """Base exception for Arzeka payment errors"""

    pass


class ArzekaConnectionError(ArzekaPaymentError):
    """Exception raised when connection to Arzeka API fails"""

    pass


class ArzekaValidationError(ArzekaPaymentError):
    """Exception raised when payment data validation fails"""

    pass


class ArzekaAPIError(ArzekaPaymentError):
    """Exception raised when Arzeka API returns an error"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ArzekaAuthenticationError(ArzekaPaymentError):
    """Exception raised when authentication fails"""

    pass
