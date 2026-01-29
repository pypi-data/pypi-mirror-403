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
