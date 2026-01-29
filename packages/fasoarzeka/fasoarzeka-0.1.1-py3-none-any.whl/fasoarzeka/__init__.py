"""
Arzeka Payment API Client
Unofficial API client for Faso Arzeka mobile money payments in Burkina Faso
"""

from importlib.metadata import version

from .base import ArzekaPayment
from .exceptions import (
    ArzekaAuthenticationError,
    ArzekaConnectionError,
    ArzekaPaymentError,
    ArzekaValidationError,
)
from .main import (
    authenticate,
    check_payment,
    check_sms_status,
    close_shared_client,
    get_shared_client,
    initiate_payment,
    send_sms,
)
from .utils import format_msisdn, generate_hash_signature, get_reference, validate_phone_number

__version__ = version("fasoarzeka")
__author__ = "Mohamed Zeba (m.zeba@mzeba.dev)"
__all__ = [
    # Classes
    "ArzekaPayment",
    # Exceptions
    "ArzekaAuthenticationError",
    "ArzekaPaymentError",
    "ArzekaValidationError",
    "ArzekaConnectionError",
    # Functions
    "initiate_payment",
    "check_payment",
    "authenticate",
    "close_shared_client",
    "get_shared_client",
    "send_sms",
    "check_sms_status",
    # Utility functions
    "get_reference",
    "format_msisdn",
    "validate_phone_number",
    "generate_hash_signature",
]
