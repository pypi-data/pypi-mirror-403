"""
Faso Arzeka Payment Gateway API Client
Unofficial API client for Arzeka mobile money payments in Burkina Faso
"""

from typing import Any, Dict, Optional, Tuple

from .base import ArzekaPayment, logger
from .constants import BASE_URL, DEFAULT_TIMEOUT
from .exceptions import ArzekaAuthenticationError

# Shared client instance for convenience functions
_shared_client: Optional[ArzekaPayment] = None
_shared_client_config: Dict[str, Any] = {}


def _get_shared_client(
    base_url: str = BASE_URL, timeout: int = DEFAULT_TIMEOUT
) -> ArzekaPayment:
    """
    Get or create a shared ArzekaPayment client instance

    Args:
        base_url: Base URL for the API
        timeout: Request timeout in seconds

    Returns:
        Shared ArzekaPayment instance
    """
    global _shared_client, _shared_client_config

    # Check if we need to create a new client or if config changed
    current_config = {"base_url": base_url, "timeout": timeout}

    if _shared_client is None or _shared_client_config != current_config:
        # Close existing client if any
        if _shared_client is not None:
            try:
                _shared_client.close()
            except Exception as e:
                logger.debug(f"Error closing previous shared client: {e}")

        # Create new client
        _shared_client = ArzekaPayment(base_url=base_url, timeout=timeout)
        _shared_client_config = current_config
        logger.debug("Created new shared ArzekaPayment client")

    return _shared_client


def get_shared_client() -> Optional[ArzekaPayment]:
    """
    Get the current shared client instance if it exists

    Returns:
        The shared ArzekaPayment instance or None if not initialized

    Example:
        >>> authenticate("user", "password")
        >>> client = get_shared_client()
        >>> if client and client.is_token_valid():
        ...     print("Shared client has valid token")
    """
    return _shared_client


def close_shared_client() -> None:
    """
    Close and cleanup the shared client instance

    Example:
        >>> authenticate("user", "password")
        >>> # ... do some operations ...
        >>> close_shared_client()  # Cleanup when done
    """
    global _shared_client, _shared_client_config

    if _shared_client is not None:
        try:
            _shared_client.close()
            logger.info("Shared client closed")
        except Exception as e:
            logger.error(f"Error closing shared client: {e}")
        finally:
            _shared_client = None
            _shared_client_config = {}


# Convenience functions using shared client instance
def authenticate(
    username: str,
    password: str,
    base_url: str = BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Authenticate and obtain access token using shared client instance

    This function uses a shared ArzekaPayment instance that persists across
    multiple function calls, allowing you to authenticate once and then use
    initiate_payment() and check_payment() without re-authenticating.

    Args:
        username: User's username or email
        password: User's password
        base_url: API base URL
        timeout: Request timeout

    Returns:
        Dictionary containing access_token, token_type, and expires_in

    Example:
        >>> # Authenticate once
        >>> auth = authenticate("user@example.com", "password123")
        >>> print(f"Token expires in {auth['expires_in']} seconds")
        >>>
        >>> # Now you can use other functions without passing credentials
        >>> payment = initiate_payment(payment_data)
        >>> status = check_payment("order-123")
    """
    client = _get_shared_client(base_url, timeout)
    return client.authenticate(username, password)


def initiate_payment(
    payment_data: Dict[str, Any],
    base_url: str = BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Initiate a payment using shared client instance

    Uses the shared ArzekaPayment instance that was authenticated with authenticate().
    If the token is expired, you need to call authenticate() again.

    Args:
        payment_data: Payment data dictionary containing:
            - amount: Payment amount
            - merchant_id: Merchant identifier
            - additional_info: Additional payment information
            - hash_secret: Hash secret for signature
            - link_for_update_status: Webhook URL
            - link_back_to_calling_website: Redirect URL
            - mapped_order_id: (optional) Transaction ID
        base_url: API base URL (default: uses same as authenticate)
        timeout: Request timeout

    Returns:
        url: URL to redirect user for payment

    Raises:
        ArzekaAuthenticationError: If not authenticated or token expired

    Example:
        >>> # First authenticate
        >>> authenticate("user", "password")
        >>>
        >>> # Then initiate payment
        >>> payment_data = {
        ...     "amount": 1000,
        ...     "merchant_id": "merchant123",
        ...     "additional_info": {...},
        ...     "hash_secret": "secret",
        ...     "link_for_update_status": "https://...",
        ...     "link_back_to_calling_website": "https://..."
        ... }
        >>> response = initiate_payment(payment_data)
    """
    client = _get_shared_client(base_url, timeout)

    # Check if authenticated
    if client._token is None:
        raise ArzekaAuthenticationError(
            "Not authenticated. Please call authenticate() first."
        )

    return client.initiate_payment(
        amount=payment_data.get("amount"),
        merchant_id=payment_data.get("merchant_id"),
        link_for_update_status=payment_data.get("link_for_update_status"),
        link_back_to_calling_website=payment_data.get("link_back_to_calling_website"),
        additional_info=payment_data.get("additional_info"),
        hash_secret=payment_data.get("hash_secret"),
        mapped_order_id=payment_data.get("mapped_order_id"),
    )


def check_payment(
    mapped_order_id: str,
    transaction_id: Optional[str] = None,
    base_url: str = BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Check payment status using shared client instance

    Uses the shared ArzekaPayment instance that was authenticated with authenticate().
    If the token is expired, you need to call authenticate() again.

    Args:
        mapped_order_id: Transaction ID to check
        transaction_id: Optional transaction ID for additional verification
        base_url: API base URL (default: uses same as authenticate)
        timeout: Request timeout

    Returns:
        Payment status data

    Raises:
        ArzekaAuthenticationError: If not authenticated or token expired

    Example:
        >>> # First authenticate
        >>> authenticate("user", "password")
        >>>
        >>> # Then check payment
        >>> status = check_payment("order-123")
        >>> print(f"Payment status: {status}")
    """
    client = _get_shared_client(base_url, timeout)

    # Check if authenticated
    if client._token is None:
        raise ArzekaAuthenticationError(
            "Not authenticated. Please call authenticate() first."
        )

    return client.check_payment(mapped_order_id, transaction_id)


def send_sms(
    mobile: str,
    message: str,
    base_url: str = BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Send an SMS using the shared client instance.

    Convenience wrapper that uses the module-level shared client. Requires
    prior authentication (call `authenticate()` first).
    """
    client = _get_shared_client(base_url, timeout)

    if client._token is None:
        raise ArzekaAuthenticationError(
            "Not authenticated. Please call authenticate() first."
        )

    return client.send_sms(mobile=mobile, message=message)


def check_sms_status(
    sms_id: str,
    base_url: str = BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Check the SMS delivery/status using the shared client instance."""
    client = _get_shared_client(base_url, timeout)

    if client._token is None:
        raise ArzekaAuthenticationError(
            "Not authenticated. Please call authenticate() first."
        )

    return client.check_sms_status(sms_id)
