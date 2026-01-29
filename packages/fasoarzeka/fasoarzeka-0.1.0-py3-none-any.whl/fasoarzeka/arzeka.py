"""
Faso Arzeka Payment Gateway API Client
Unofficial API client for Arzeka mobile money payments in Burkina Faso
"""

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    ArzekaAPIError,
    ArzekaAuthenticationError,
    ArzekaConnectionError,
    ArzekaPaymentError,
    ArzekaValidationError,
)
from .utils import generate_hash_signature, get_reference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://pgw-test.fasoarzeka.bf/"

PAYMENT_BASE_URL = "AvepayPaymentGatewayUI/avepay-payment/"
INITIATE_PAYMENT_ENDPOINT = "app/initializePayment"
AUTH_ENDPOINT = "auth/getToken"
PAYMENT_VERIFICATION_ENDPOINT = "app/getThirdPartyMapInfo"

SMS_BASE_URL = "ArzekaSmsSender/"
SEND_SMS = "sendSms"
CHECK_SMS_STATUS = "checkSms"


DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
MINIMUM_AMOUNT = 100  # Minimum payment amount in Franc CFA (XOF)
EXPIRATION_MARGIN_SECONDS = 2 * 60  # Default margin for token validity checks


class BasePayment:
    """
    Base class for Arzeka payment operations

    Attributes:

        base_url (str): Base URL for the Arzeka API
        timeout (int): Request timeout in seconds
    """

    def __init__(self, base_url: str = BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the BasePayment client

        Args:
            base_url: Base URL for the API (default: test environment)
            timeout: Request timeout in seconds

        Raises:
            ArzekaValidationError: If token is invalid
        """

        self._token: str = None
        self._token_type: str = None
        self._expires_at: float = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self._session = self._create_session()

        logger.info("Arzeka payment client initialized")

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        # session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(
        self, additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Get request headers with optional additional headers

        Args:
            additional_headers: Optional dictionary of additional headers

        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "arzeka-payment-client/1.0",
            "Accept-Language": "fr-FR,en-GB;q=0.8,en;q=0.6",
            "Authorization": f"{self._token_type} {self._token}",
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Arzeka API

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            data: Request body data (for POST)
            params: URL parameters (for GET)
            **kwargs: Additional arguments for requests

        Returns:
            Response data as dictionary

        Raises:
            ArzekaConnectionError: If connection fails
            ArzekaAPIError: If API returns an error
        """

        if self._token is None or self._expires_at is None:
            raise ArzekaAuthenticationError(
                "Authentication token is not set. Please authenticate first."
            )

        url = urljoin(self.base_url, endpoint)
        headers = kwargs.pop("headers", {})
        headers = self._get_headers(headers)

        timeout = kwargs.pop("timeout", self.timeout)

        try:
            logger.debug(f"Making {method} request to {url}")

            if method.upper() == "POST":
                response = self._session.post(
                    url, data=data, headers=headers, timeout=timeout, **kwargs
                )
            elif method.upper() == "GET":
                response = self._session.get(
                    url, params=params, headers=headers, timeout=timeout, **kwargs
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"raw_response": response.text}

            logger.info(f"Request successful: {method} {url}")
            return response_data

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise ArzekaConnectionError(
                f"Request timeout after {timeout} seconds"
            ) from e

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ArzekaConnectionError(f"Failed to connect to Arzeka API: {e}") from e

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"error": response.text}

            raise ArzekaAPIError(
                f"API request failed: {e}",
                status_code=response.status_code,
                response_data=error_data,
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ArzekaPaymentError(f"Unexpected error: {e}") from e

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Make POST request to Arzeka API

        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional arguments

        Returns:
            Response data
        """
        return self._make_request("POST", endpoint, data=data, **kwargs)

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Make GET request to Arzeka API

        Args:
            endpoint: API endpoint
            params: URL parameters
            **kwargs: Additional arguments

        Returns:
            Response data
        """
        return self._make_request("GET", endpoint, params=params, **kwargs)

    def close(self):
        """Close the session"""
        if self._session:
            self._session.close()
            logger.info("Session closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class ArzekaPayment(BasePayment):
    """
    Arzeka Payment Gateway client

    Provides methods to initiate and check payment status
    """

    def __init__(self, base_url: str = BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize Arzeka Payment client

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, timeout)

    def is_token_valid(self, margin_seconds: int = EXPIRATION_MARGIN_SECONDS) -> bool:
        """
        Check if the authentication token is still valid

        Args:
            margin_seconds: Safety margin in seconds before actual expiration.
                          Default is 60 seconds. The token is considered expired
                          if it will expire within this margin.

        Returns:
            bool: True if token is valid and not expired, False otherwise

        Example:
            >>> client = ArzekaPayment()
            >>> client.authenticate("user", "password")
            >>> if client.is_token_valid():
            ...     print("Token is valid")
            ... else:
            ...     print("Token expired, need to reauthenticate")

            >>> # Check with custom margin (5 minutes before expiration)
            >>> if client.is_token_valid(margin_seconds=300):
            ...     print("Token valid for at least 5 more minutes")
        """
        # Check if token exists
        if self._token is None:
            logger.debug("No token available")
            return False

        # Check if expiration timestamp is set
        if self._expires_at is None or self._expires_at == 0:
            logger.debug("No expiration timestamp available")
            return False

        # Get current timestamp in UTC (même timezone que le serveur)
        current_time = datetime.now(timezone.utc).timestamp()

        # Calculate time until expiration
        time_until_expiry = self._expires_at - current_time

        # Check if token is still valid (considering the margin)
        is_valid = time_until_expiry > margin_seconds

        return is_valid

    def get_token_expiry_info(self) -> Dict[str, Any]:
        """
        Get detailed information about token expiration

        Returns:
            Dictionary containing:
                - is_valid (bool): Whether the token is currently valid
                - expires_at (float): Timestamp when token expires
                - expires_in_seconds (float): Seconds until expiration (negative if expired)
                - expires_in_minutes (float): Minutes until expiration
                - is_expired (bool): Whether the token has already expired
                - has_token (bool): Whether a token is present

        Example:
            >>> client = ArzekaPayment()
            >>> client.authenticate("user", "password")
            >>> info = client.get_token_expiry_info()
            >>> print(f"Token expires in {info['expires_in_minutes']:.1f} minutes")
            >>> print(f"Is valid: {info['is_valid']}")
        """
        current_time = datetime.now(timezone.utc).timestamp()

        if self._token is None:
            return {
                "is_valid": False,
                "expires_at": None,
                "expires_in_seconds": 0,
                "expires_in_minutes": 0,
                "is_expired": True,
                "has_token": False,
            }

        if self._expires_at is None or self._expires_at == 0:
            return {
                "is_valid": False,
                "expires_at": None,
                "expires_in_seconds": 0,
                "expires_in_minutes": 0,
                "is_expired": True,
                "has_token": True,
            }

        time_until_expiry = self._expires_at - current_time

        return {
            "is_valid": self.is_token_valid(),
            "expires_at": self._expires_at,
            "expires_in_seconds": time_until_expiry,
            "expires_in_minutes": time_until_expiry / 60,
            "is_expired": time_until_expiry <= 0,
            "has_token": True,
        }

    def _ensure_valid_token(self) -> None:
        """
        Ensure the token is valid, re-authenticating if necessary

        This method checks if the current token is still valid.
        If not, it automatically re-authenticates using stored credentials.

        Raises:
            ArzekaAuthenticationError: If no credentials are stored or re-authentication fails

        Example:
            >>> client = ArzekaPayment()
            >>> client.authenticate("user", "password")
            >>> # Some time later...
            >>> client._ensure_valid_token()  # Will re-authenticate if token expired
        """
        # Check if token is valid
        if self.is_token_valid():
            logger.debug("Token is still valid")
            return

        # Token is invalid or expired, need to re-authenticate
        logger.info("Token expired or invalid, attempting to re-authenticate")

        # Check if we have stored credentials
        if not self._username or not self._password:
            raise ArzekaAuthenticationError(
                "Token expired and no credentials stored for automatic re-authentication. "
                "Please call authenticate() again with username and password."
            )

        # Re-authenticate
        try:
            self.authenticate(self._username, self._password)
            logger.info("Successfully re-authenticated")
        except Exception as e:
            logger.error(f"Failed to re-authenticate: {e}")
            raise ArzekaAuthenticationError(
                f"Automatic re-authentication failed: {e}"
            ) from e

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Arzeka API to obtain an access token

        Args:
            username: User's username or email
            password: User's password

        Returns:
            Dictionary containing:
                - access_token (str): The JWT access token
                - token_type (str): Type of token (usually "Bearer")
                - expires_in (int): Token expiration time in seconds

        Raises:
            ArzekaValidationError: If credentials are invalid
            ArzekaAuthenticationError: If authentication fails
            ArzekaAPIError: If API request fails

        Example:
            >>> client = ArzekaPayment(token="")
            >>> auth_response = client.authenticate("user@example.com", "password123")
            >>> print(f"Token: {auth_response['access_token']}")
            >>> print(f"Expires in: {auth_response['expires_in']} seconds")
        """
        # Validate inputs
        if not username or not isinstance(username, str):
            raise ArzekaValidationError("username must be a non-empty string")

        if not password or not isinstance(password, str):
            raise ArzekaValidationError("password must be a non-empty string")

        # Prepare authentication data
        auth_data = {
            "username": username,
            "password": password,
            "grant_type": "access_token",
        }

        logger.info(f"Attempting authentication for user: {username}")

        try:
            # Make API request without requiring prior authentication
            # Temporarily override headers to exclude Authorization
            url = urljoin(self.base_url, PAYMENT_BASE_URL + AUTH_ENDPOINT)
            logger.info(f"Sending authentication request to {url}")
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "fasoarzeka-client",
                "Accept-Language": "fr-FR,en-GB;q=0.8,en;q=0.6",
            }

            response = self._session.post(
                url,
                data=auth_data,
                headers=headers,
                timeout=self.timeout,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            try:
                response_data = response.json()
            except ValueError:
                logger.error("Failed to parse authentication response")
                raise ArzekaAuthenticationError(
                    "Invalid response format from authentication endpoint"
                )
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"JSON decode error during authentication: {e}")
                raise ArzekaAuthenticationError(
                    "Invalid JSON response from authentication endpoint"
                ) from e

            # Validate response contains required fields
            if "access_token" not in response_data:
                logger.error("Authentication response missing access_token")
                raise ArzekaAuthenticationError(
                    "Authentication response missing required fields"
                )

            # Update the client's token if authentication successful
            if response_data.get("access_token"):
                self._token = response_data["access_token"]
                self._expires_at = datetime.now(timezone.utc).timestamp() + float(
                    response_data["expires_in"]
                )
                # Store credentials for automatic re-authentication
                self._username = username
                self._password = password
                self._token_type = response_data.get("token_type", "Bearer")

                logger.info(f"Authentication successful for user: {username}")

            return {
                "access_token": response_data.get("access_token"),
                "token_type": response_data.get("token_type", "Bearer"),
                "expires_in": response_data.get("expires_in", 3600),
                "expires_at": self._expires_at,
            }

        except requests.exceptions.HTTPError as e:
            logger.error(f"Authentication failed: {e}")

            # Handle authentication errors
            try:
                error_data = response.json()
            except requests.exceptions.JSONDecodeError:
                error_data = {"error": response.text}
            raise ArzekaAPIError(
                f"Authentication request failed: {e}",
                status_code=response.status_code,
                response_data=error_data,
            ) from e

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during authentication: {e}")
            raise ArzekaConnectionError(
                f"Failed to connect to authentication endpoint: {e}"
            ) from e

        except requests.exceptions.Timeout as e:
            logger.error(f"Authentication timeout: {e}")
            raise ArzekaConnectionError(
                f"Authentication request timeout after {self.timeout} seconds"
            ) from e

        except ArzekaPaymentError:
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise ArzekaAuthenticationError(
                f"Authentication failed with unexpected error: {e}"
            ) from e

    def initiate_payment(
        self,
        amount: float,
        merchant_id: str,
        link_for_update_status: str,
        link_back_to_calling_website: str,
        additional_info: Dict[str, Any],
        hash_secret: str,
        mapped_order_id: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Initiate a payment transaction

        Args:
            amount: Payment amount
            merchant_id: Merchant identifier
            mapped_order_id: Unique transaction ID (auto-generated if not provided)
            link_for_update_status: Webhook URL for status updates
            link_back_to_calling_website: Redirect URL after payment
            additional_info: Additional payment information
            hash_secret: Secret key for generating hash signature


        Returns:
            url: URL to redirect user for payment

        Raises:
            ArzekaValidationError: If required parameters are invalid
            ArzekaAPIError: If API request fails
        """
        # Ensure token is valid before making the request
        self._ensure_valid_token()

        # Validate inputs
        if not isinstance(amount, (int, float)) or amount <= MINIMUM_AMOUNT:
            raise ArzekaValidationError(
                f"amount must be a positive number greater than {MINIMUM_AMOUNT}"
            )

        if not merchant_id or not isinstance(merchant_id, (str, int)):
            raise ArzekaValidationError("merchant_id must be a non-empty string/int")

        if not set(["firstname", "lastname", "mobile"]).issubset(
            additional_info.keys()
        ):
            raise ArzekaValidationError(
                "additional_info must contain firstname, lastname, and mobile"
            )

        if (
            not additional_info.get("firstname", None)
            or not additional_info.get("lastname", None)
            or not additional_info.get("mobile", None)
        ):
            raise ArzekaValidationError(
                "additional_info fields firstname, lastname, and mobile cannot be empty or null"
            )

        if "generateReceipt" not in additional_info:
            additional_info["generateReceipt"] = False
            additional_info["paymentDescription"] = ""
            additional_info["accountingOffice"] = ""
            additional_info["accountantName"] = ""
            additional_info["address"] = ""
        elif (
            "generateReceipt" in additional_info and additional_info["generateReceipt"]
        ):
            required_receipt_fields = [
                "paymentDescription",
                "accountingOffice",
                "accountantName",
            ]
            if not set(required_receipt_fields).issubset(additional_info.keys()):
                raise ArzekaValidationError(
                    f"When generateReceipt is True, additional_info must contain: {', '.join(required_receipt_fields)}"
                )

        # Generate order ID if not provided
        if not mapped_order_id:
            mapped_order_id = get_reference()
            logger.info(f"Generated order ID: {mapped_order_id}")

        # Prepare payment data
        payment_data = {
            "amount": amount,
            "merchantId": merchant_id,
            "mappedOrderId": mapped_order_id,
            "additionalInfo": json.dumps(additional_info, separators=(",", ":")),
            "linkForUpdateStatus": base64.b64encode(
                link_for_update_status.encode()
            ).decode(),
            "linkBackToCallingWebsite": base64.b64encode(
                link_back_to_calling_website.encode()
            ).decode(),
        }

        hash_string = generate_hash_signature(hash_secret=hash_secret, **payment_data)
        payment_data["hashString"] = hash_string

        logger.info(
            f"Initiating payment for order: {mapped_order_id}, amount: {amount}"
        )

        # Make API request
        response = self.post(
            PAYMENT_BASE_URL + INITIATE_PAYMENT_ENDPOINT, data=payment_data
        )

        logger.info(f"Payment initiated successfully: {mapped_order_id}")
        return response, payment_data

    def check_payment(
        self, mapped_order_id: str, transaction_id: str = None
    ) -> Dict[str, Any]:
        """
        Check payment transaction status

        Args:
            mapped_order_id: Transaction ID to check
            **kwargs: Additional parameters

        Returns:
            Payment status data

        Raises:
            ArzekaValidationError: If order ID is invalid
            ArzekaAPIError: If API request fails
        """
        # Ensure token is valid before making the request
        self._ensure_valid_token()

        if not mapped_order_id or not isinstance(mapped_order_id, str):
            raise ArzekaValidationError("mapped_order_id must be a non-empty string")

        logger.info(f"Checking payment status for order: {mapped_order_id}")

        # Prepare query parameters
        url = (
            PAYMENT_BASE_URL
            + PAYMENT_VERIFICATION_ENDPOINT
            + f"?mappedOrderId={mapped_order_id}"
        )

        if transaction_id:
            url += f"&transId={transaction_id}"

        # Make API request
        response = self.post(url)

        logger.info(f"Payment status retrieved for order: {mapped_order_id}")
        return response

    def send_sms(
        self,
        mobile: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send an SMS using the Arzeka SMS sender endpoint

        Args:
            mobile: Recipient phone number (string)
            message: SMS message content
            sender: Optional sender identifier
            **kwargs: Additional parameters forwarded to the SMS API

        Returns:
            Response data from the SMS API as a dict

        Raises:
            ArzekaValidationError: If inputs are invalid
            ArzekaAPIError / ArzekaConnectionError: On request failures
        """
        # Ensure authentication
        self._ensure_valid_token()

        if not mobile or not isinstance(mobile, str):
            raise ArzekaValidationError("mobile must be a non-empty string")

        if not message or not isinstance(message, str):
            raise ArzekaValidationError("message must be a non-empty string")

        data: Dict[str, Any] = {"msisdn": mobile, "message": message}

        # Use existing request wrapper to benefit from shared headers/retries/errors
        return self.post(SMS_BASE_URL + SEND_SMS, data=data)

    def check_sms_status(self, sms_id: str) -> Dict[str, Any]:
        """Check the delivery/status of a previously sent SMS

        Args:
            sms_id: Identifier of the SMS to check

        Returns:
            Response data from the SMS status API as a dict
        """
        self._ensure_valid_token()

        if not sms_id or not isinstance(sms_id, str):
            raise ArzekaValidationError("sms_id must be a non-empty string")

        return self.get(SMS_BASE_URL + CHECK_SMS_STATUS + f"?referenceid={sms_id}")


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
