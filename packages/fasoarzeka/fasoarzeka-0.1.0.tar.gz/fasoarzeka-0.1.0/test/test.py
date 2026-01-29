"""
Tests unitaires pour l'authentification et la vérification de paiement
Arzeka Payment API Client
"""

import time
import unittest
from unittest.mock import Mock, patch

import requests

from fasoarzeka import (
    ArzekaAuthenticationError,
    ArzekaPayment,
    ArzekaValidationError,
    authenticate,
    initiate_payment,
    check_payment,
    close_shared_client,
    get_shared_client,
)


class TestAuthentication(unittest.TestCase):
    """Tests pour l'authentification"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.client = ArzekaPayment()

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.client.close()

    def test_authenticate_validation_empty_username(self):
        """Test validation d'authentification avec username vide"""
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate("", "password")

    def test_authenticate_validation_empty_password(self):
        """Test validation d'authentification avec password vide"""
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate("username", "")

    def test_authenticate_validation_none_username(self):
        """Test validation d'authentification avec username None"""
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate(None, "password")

    def test_authenticate_validation_none_password(self):
        """Test validation d'authentification avec password None"""
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate("username", None)

    @patch("arzeka.requests.Session.post")
    def test_authenticate_success(self, mock_post):
        """Test d'authentification réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_abc123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.authenticate("test_user", "test_password")

        # Vérifier le résultat de la réponse
        self.assertEqual(result["access_token"], "token_abc123")
        self.assertEqual(result["token_type"], "Bearer")
        self.assertEqual(result["expires_in"], 3600)

        # Vérifier que le client a stocké les informations
        self.assertEqual(self.client._token, "token_abc123")
        self.assertEqual(self.client._username, "test_user")
        self.assertEqual(self.client._password, "test_password")
        self.assertIsNotNone(self.client._expires_at)

    @patch("arzeka.requests.Session.post")
    def test_authenticate_invalid_credentials(self, mock_post):
        """Test d'authentification avec identifiants invalides"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid credentials"}
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("401 Unauthorized")
        )

        with self.assertRaises(ArzekaAuthenticationError):
            self.client.authenticate("wrong_user", "wrong_password")

    @patch("arzeka.requests.Session.post")
    def test_authenticate_server_error(self, mock_post):
        """Test d'authentification avec erreur serveur (500)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("500 Server Error")
        )

        with self.assertRaises(ArzekaAuthenticationError):
            self.client.authenticate("test_user", "test_password")

    def test_is_token_valid_no_token(self):
        """Test de validité du token quand il n'y a pas de token"""
        self.assertFalse(self.client.is_token_valid())

    def test_is_token_valid_with_valid_token(self):
        """Test de validité du token avec un token valide"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() + 3600  # Expire dans 1 heure
        self.assertTrue(self.client.is_token_valid())

    def test_is_token_valid_with_expired_token(self):
        """Test de validité du token avec un token expiré"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() - 100  # Expiré il y a 100 secondes
        self.assertFalse(self.client.is_token_valid())

    def test_is_token_valid_with_margin(self):
        """Test de validité du token avec marge personnalisée"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() + 30  # Expire dans 30 secondes

        # Avec marge par défaut (60s), devrait être invalide
        self.assertFalse(self.client.is_token_valid())

        # Avec marge de 10s, devrait être valide
        self.assertTrue(self.client.is_token_valid(margin_seconds=10))

    def test_get_token_expiry_info_no_token(self):
        """Test d'info d'expiration sans token"""
        info = self.client.get_token_expiry_info()
        self.assertFalse(info["is_valid"])
        self.assertFalse(info["has_token"])
        self.assertTrue(info["is_expired"])
        self.assertIsNone(info["expires_at"])

    def test_get_token_expiry_info_with_valid_token(self):
        """Test d'info d'expiration avec token valide"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() + 3600

        info = self.client.get_token_expiry_info()
        self.assertTrue(info["is_valid"])
        self.assertTrue(info["has_token"])
        self.assertFalse(info["is_expired"])
        self.assertIsNotNone(info["expires_at"])
        self.assertGreater(info["expires_in_seconds"], 0)
        self.assertGreater(info["expires_in_minutes"], 0)

    @patch.object(ArzekaPayment, "authenticate")
    def test_ensure_valid_token_with_valid_token(self, mock_auth):
        """Test _ensure_valid_token avec token valide"""
        self.client._token = "valid_token"
        self.client._expires_at = time.time() + 3600

        # Ne devrait pas appeler authenticate
        self.client._ensure_valid_token()
        mock_auth.assert_not_called()

    def test_ensure_valid_token_no_credentials(self):
        """Test _ensure_valid_token sans credentials stockés"""
        self.client._token = "expired_token"
        self.client._expires_at = time.time() - 100

        with self.assertRaises(ArzekaAuthenticationError) as context:
            self.client._ensure_valid_token()

        self.assertIn("no credentials stored", str(context.exception))

    @patch.object(ArzekaPayment, "authenticate")
    def test_ensure_valid_token_auto_reauth(self, mock_auth):
        """Test de réauthentification automatique quand token expiré"""
        self.client._token = "expired_token"
        self.client._expires_at = time.time() - 100
        self.client._username = "test_user"
        self.client._password = "test_pass"

        # Mock authenticate pour qu'il mette à jour le token
        def update_token(username, password):
            self.client._token = "new_token"
            self.client._expires_at = time.time() + 3600
            return {
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }

        mock_auth.side_effect = update_token

        self.client._ensure_valid_token()
        mock_auth.assert_called_once_with("test_user", "test_pass")
        self.assertEqual(self.client._token, "new_token")


class TestPaymentVerification(unittest.TestCase):
    """Tests pour la vérification de paiement"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.client = ArzekaPayment()
        # Simule un client authentifié
        self.client._token = "valid_token"
        self.client._expires_at = time.time() + 3600

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.client.close()

    def test_check_payment_validation_empty_order_id(self):
        """Test validation de vérification avec order_id vide"""
        with self.assertRaises(ArzekaValidationError):
            self.client.check_payment(mapped_order_id="")

    def test_check_payment_validation_none_order_id(self):
        """Test validation de vérification avec order_id None"""
        with self.assertRaises(ArzekaValidationError):
            self.client.check_payment(mapped_order_id=None)

    @patch.object(ArzekaPayment, "_ensure_valid_token")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_success(self, mock_post, mock_ensure):
        """Test de vérification de paiement réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "completed",
            "mappedOrderId": "ORDER123",
            "amount": 1000,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.check_payment(mapped_order_id="ORDER123")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mappedOrderId"], "ORDER123")
        self.assertEqual(result["amount"], 1000)
        mock_ensure.assert_called_once()
        mock_post.assert_called_once()

    @patch.object(ArzekaPayment, "_ensure_valid_token")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_pending(self, mock_post, mock_ensure):
        """Test de vérification de paiement en attente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "pending",
            "mappedOrderId": "ORDER124",
            "amount": 1500,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.check_payment(mapped_order_id="ORDER124")

        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["mappedOrderId"], "ORDER124")

    @patch.object(ArzekaPayment, "_ensure_valid_token")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_failed(self, mock_post, mock_ensure):
        """Test de vérification de paiement échoué"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "failed",
            "mappedOrderId": "ORDER125",
            "reason": "Payment rejected",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.check_payment(mapped_order_id="ORDER125")

        self.assertEqual(result["status"], "failed")
        self.assertIn("reason", result)

    @patch.object(ArzekaPayment, "_ensure_valid_token")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_api_error(self, mock_post, mock_ensure):
        """Test de vérification de paiement avec erreur API"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Order not found"}
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("404 Not Found")
        )

        with self.assertRaises(Exception):
            self.client.check_payment(mapped_order_id="INVALID_ORDER")


class TestSharedClientAuthentication(unittest.TestCase):
    """Tests pour l'authentification avec client partagé"""

    def setUp(self):
        """Configuration avant chaque test"""
        close_shared_client()

    def tearDown(self):
        """Nettoyage après chaque test"""
        close_shared_client()

    @patch("arzeka.requests.Session.post")
    def test_authenticate_function_success(self, mock_post):
        """Test de la fonction authenticate réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "shared_token_xyz",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = authenticate("test_user", "test_password")

        self.assertEqual(result["access_token"], "shared_token_xyz")
        self.assertEqual(result["token_type"], "Bearer")

        # Vérifier que le client partagé a été créé et authentifié
        client = get_shared_client()
        self.assertIsNotNone(client)
        self.assertEqual(client._token, "shared_token_xyz")

    def test_authenticate_function_validation_error(self):
        """Test validation de la fonction authenticate"""
        with self.assertRaises(ArzekaValidationError):
            authenticate("", "password")

    @patch("arzeka.requests.Session.post")
    def test_get_shared_client_before_auth(self, mock_post):
        """Test récupération du client partagé avant authentification"""
        self.assertIsNone(get_shared_client())

    @patch("arzeka.requests.Session.post")
    def test_get_shared_client_after_auth(self, mock_post):
        """Test récupération du client partagé après authentification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_shared",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        authenticate("user", "pass")

        client = get_shared_client()
        self.assertIsNotNone(client)
        self.assertIsInstance(client, ArzekaPayment)
        self.assertEqual(client._token, "token_shared")

    @patch("arzeka.requests.Session.post")
    def test_close_shared_client(self, mock_post):
        """Test fermeture du client partagé"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_close",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        authenticate("user", "pass")
        self.assertIsNotNone(get_shared_client())

        close_shared_client()
        self.assertIsNone(get_shared_client())

        # Appeler close à nouveau ne devrait pas causer d'erreur
        close_shared_client()


class TestCheckPaymentSharedClient(unittest.TestCase):
    """Tests pour vérification de paiement avec client partagé"""

    def setUp(self):
        """Configuration avant chaque test"""
        close_shared_client()

    def tearDown(self):
        """Nettoyage après chaque test"""
        close_shared_client()

    @patch("arzeka.requests.Session.post")
    def test_check_payment_function_not_authenticated(self, mock_post):
        """Test check_payment sans authentification"""
        with self.assertRaises(ArzekaAuthenticationError):
            check_payment("ORDER123")

    @patch.object(ArzekaPayment, "check_payment")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_function_authenticated(self, mock_post, mock_check):
        """Test de la fonction check_payment avec authentification"""
        # D'abord authentifier
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "access_token": "token_456",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        auth_response.raise_for_status = Mock()

        mock_post.return_value = auth_response
        authenticate("user", "pass")

        # Mock de check_payment
        mock_check.return_value = {
            "status": "completed",
            "mappedOrderId": "ORDER456",
            "amount": 2000,
        }

        result = check_payment("ORDER456")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mappedOrderId"], "ORDER456")
        self.assertEqual(result["amount"], 2000)
        mock_check.assert_called_once_with("ORDER456", None)


class TestAuthenticationAndPaymentFlow(unittest.TestCase):
    """Tests de scénarios d'authentification et vérification de paiement"""

    def setUp(self):
        """Configuration avant chaque test"""
        close_shared_client()

    def tearDown(self):
        """Nettoyage après chaque test"""
        close_shared_client()

    @patch("arzeka.requests.Session.post")
    def test_authenticate_then_verify_payment(self, mock_post):
        """Test du flux complet: authentification puis vérification de paiement"""
        # 1. Authentification
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "access_token": "flow_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        auth_response.raise_for_status = Mock()

        # 2. Vérification du paiement
        check_response = Mock()
        check_response.status_code = 200
        check_response.json.return_value = {
            "status": "completed",
            "mappedOrderId": "FLOW123",
            "amount": 1500,
        }
        check_response.raise_for_status = Mock()

        mock_post.side_effect = [auth_response, check_response]

        # Exécuter le flux
        client = ArzekaPayment()

        # Authentification
        auth_result = client.authenticate("user", "pass")
        self.assertEqual(auth_result["access_token"], "flow_token")
        self.assertTrue(client.is_token_valid())

        # Vérification du paiement
        check_result = client.check_payment("FLOW123")
        self.assertEqual(check_result["status"], "completed")
        self.assertEqual(check_result["mappedOrderId"], "FLOW123")

        client.close()

    @patch("arzeka.requests.Session.post")
    @patch.object(ArzekaPayment, "authenticate")
    def test_auto_reauth_on_check_payment(self, mock_auth, mock_post):
        """Test de réauthentification automatique lors de check_payment"""
        client = ArzekaPayment()

        # Simuler une authentification initiale avec token expiré
        client._token = "expired_token"
        client._expires_at = time.time() - 100
        client._username = "user"
        client._password = "pass"

        # Mock de la réauthentification
        def reauth(username, password):
            client._token = "new_token"
            client._expires_at = time.time() + 3600
            return {
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }

        mock_auth.side_effect = reauth

        # Mock de la réponse de vérification de paiement
        check_response = Mock()
        check_response.status_code = 200
        check_response.json.return_value = {
            "status": "completed",
            "mappedOrderId": "AUTO123",
            "amount": 1000,
        }
        check_response.raise_for_status = Mock()
        mock_post.return_value = check_response

        # Faire une vérification qui devrait déclencher la réauthentification
        result = client.check_payment("AUTO123")

        # Vérifier que la réauthentification a été appelée
        mock_auth.assert_called_once_with("user", "pass")
        self.assertEqual(client._token, "new_token")
        self.assertEqual(result["status"], "completed")

        client.close()


class TestArzekaPayment(unittest.TestCase):
    """Tests pour la classe ArzekaPayment"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.client = ArzekaPayment()

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.client.close()

    def test_init(self):
        """Test d'initialisation"""
        self.assertIsNone(self.client._token)
        self.assertIsNone(self.client._expires_at)
        self.assertIsNotNone(self.client._session)

    def test_is_token_valid_no_token(self):
        """Test de validité du token quand il n'y a pas de token"""
        self.assertFalse(self.client.is_token_valid())

    def test_is_token_valid_with_valid_token(self):
        """Test de validité du token avec un token valide"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() + 3600  # Expire dans 1 heure
        self.assertTrue(self.client.is_token_valid())

    def test_is_token_valid_with_expired_token(self):
        """Test de validité du token avec un token expiré"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() - 100  # Expiré il y a 100 secondes
        self.assertFalse(self.client.is_token_valid())

    def test_is_token_valid_with_margin(self):
        """Test de validité du token avec marge personnalisée"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() + 30  # Expire dans 30 secondes

        # Avec marge par défaut (60s), devrait être invalide
        self.assertFalse(self.client.is_token_valid())

        # Avec marge de 10s, devrait être valide
        self.assertTrue(self.client.is_token_valid(margin_seconds=10))

    def test_get_token_expiry_info_no_token(self):
        """Test d'info d'expiration sans token"""
        info = self.client.get_token_expiry_info()
        self.assertFalse(info["is_valid"])
        self.assertFalse(info["has_token"])
        self.assertTrue(info["is_expired"])
        self.assertIsNone(info["expires_at"])

    def test_get_token_expiry_info_with_valid_token(self):
        """Test d'info d'expiration avec token valide"""
        self.client._token = "test_token"
        self.client._expires_at = time.time() + 3600

        info = self.client.get_token_expiry_info()
        self.assertTrue(info["is_valid"])
        self.assertTrue(info["has_token"])
        self.assertFalse(info["is_expired"])
        self.assertIsNotNone(info["expires_at"])
        self.assertGreater(info["expires_in_seconds"], 0)
        self.assertGreater(info["expires_in_minutes"], 0)

    @patch("arzeka.requests.Session.post")
    def test_authenticate_success(self, mock_post):
        """Test d'authentification réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_abc123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.authenticate("test_user", "test_password")

        self.assertEqual(result["access_token"], "token_abc123")
        self.assertEqual(result["token_type"], "Bearer")
        self.assertEqual(result["expires_in"], 3600)
        self.assertEqual(self.client._token, "token_abc123")
        self.assertEqual(self.client._username, "test_user")
        self.assertEqual(self.client._password, "test_password")
        self.assertIsNotNone(self.client._expires_at)

    def test_authenticate_validation_errors(self):
        """Test des erreurs de validation d'authentification"""
        # Username vide
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate("", "password")

        # Password vide
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate("username", "")

        # Username non-string
        with self.assertRaises(ArzekaValidationError):
            self.client.authenticate(None, "password")

    @patch("arzeka.requests.Session.post")
    def test_authenticate_http_401_error(self, mock_post):
        """Test d'erreur 401 lors de l'authentification"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid credentials"}
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError()
        )

        with self.assertRaises(ArzekaAuthenticationError) as context:
            self.client.authenticate("wrong_user", "wrong_password")

        self.assertIn("Invalid credentials", str(context.exception))

    def test_ensure_valid_token_no_credentials(self):
        """Test _ensure_valid_token sans credentials stockés"""
        self.client._token = "expired_token"
        self.client._expires_at = time.time() - 100

        with self.assertRaises(ArzekaAuthenticationError) as context:
            self.client._ensure_valid_token()

        self.assertIn("no credentials stored", str(context.exception))

    @patch.object(ArzekaPayment, "authenticate")
    def test_ensure_valid_token_with_valid_token(self, mock_auth):
        """Test _ensure_valid_token avec token valide"""
        self.client._token = "valid_token"
        self.client._expires_at = time.time() + 3600

        # Ne devrait pas appeler authenticate
        self.client._ensure_valid_token()
        mock_auth.assert_not_called()

    @patch.object(ArzekaPayment, "authenticate")
    def test_ensure_valid_token_auto_reauth(self, mock_auth):
        """Test de réauthentification automatique"""
        self.client._token = "expired_token"
        self.client._expires_at = time.time() - 100
        self.client._username = "test_user"
        self.client._password = "test_pass"

        # Mock authenticate pour qu'il mette à jour le token
        def update_token(username, password):
            self.client._token = "new_token"
            self.client._expires_at = time.time() + 3600
            return {
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }

        mock_auth.side_effect = update_token

        self.client._ensure_valid_token()
        mock_auth.assert_called_once_with("test_user", "test_pass")

    def test_initiate_payment_validation_amount(self):
        """Test de validation du montant de paiement"""
        payment_data = {
            "merchant_id": "TEST123",
            "additional_info": {
                "first_name": "John",
                "last_name": "Doe",
                "mobile": "70123456",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        # Montant trop petit
        with self.assertRaises(ArzekaValidationError):
            self.client.initiate_payment(amount=50, **payment_data)

        # Montant négatif
        with self.assertRaises(ArzekaValidationError):
            self.client.initiate_payment(amount=-100, **payment_data)

    def test_initiate_payment_validation_merchant_id(self):
        """Test de validation du merchant_id"""
        payment_data = {
            "amount": 1000,
            "additional_info": {
                "first_name": "John",
                "last_name": "Doe",
                "mobile": "70123456",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        with self.assertRaises(ArzekaValidationError):
            self.client.initiate_payment(merchant_id="", **payment_data)

    def test_initiate_payment_validation_additional_info(self):
        """Test de validation des additional_info"""
        payment_data = {
            "amount": 1000,
            "merchant_id": "TEST123",
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        # Manque first_name
        with self.assertRaises(ArzekaValidationError):
            self.client.initiate_payment(
                additional_info={"last_name": "Doe", "mobile": "70123456"},
                **payment_data,
            )

    @patch.object(ArzekaPayment, "_ensure_valid_token")
    @patch("arzeka.requests.Session.post")
    def test_initiate_payment_success(self, mock_post, mock_ensure):
        """Test de paiement réussi"""
        # Setup
        self.client._token = "valid_token"
        self.client._expires_at = time.time() + 3600

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "mappedOrderId": "ORDER123",
            "paymentUrl": "https://pay.example.com/ORDER123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        payment_data = {
            "amount": 1000,
            "merchant_id": "TEST123",
            "additional_info": {
                "first_name": "John",
                "last_name": "Doe",
                "mobile": "70123456",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        result = self.client.initiate_payment(**payment_data)

        self.assertEqual(result["status"], "success")
        self.assertIn("mappedOrderId", result)
        mock_ensure.assert_called_once()
        mock_post.assert_called_once()

    def test_check_payment_validation(self):
        """Test de validation pour vérification de paiement"""
        with self.assertRaises(ArzekaValidationError):
            self.client.check_payment(mapped_order_id="")

        with self.assertRaises(ArzekaValidationError):
            self.client.check_payment(mapped_order_id=None)

    @patch.object(ArzekaPayment, "_ensure_valid_token")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_success(self, mock_post, mock_ensure):
        """Test de vérification de paiement réussie"""
        self.client._token = "valid_token"
        self.client._expires_at = time.time() + 3600

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "completed",
            "mappedOrderId": "ORDER123",
            "amount": 1000,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.check_payment(mapped_order_id="ORDER123")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mappedOrderId"], "ORDER123")
        mock_ensure.assert_called_once()
        mock_post.assert_called_once()


class TestConvenienceFunctions(unittest.TestCase):
    """Tests pour les fonctions de commodité"""

    def setUp(self):
        """Configuration avant chaque test"""
        # Nettoyer le client partagé avant chaque test
        close_shared_client()

    def tearDown(self):
        """Nettoyage après chaque test"""
        close_shared_client()

    @patch("arzeka.requests.Session.post")
    def test_authenticate_function(self, mock_post):
        """Test de la fonction authenticate"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_xyz789",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = authenticate("test_user", "test_password")

        self.assertEqual(result["access_token"], "token_xyz789")
        self.assertEqual(result["token_type"], "Bearer")
        self.assertEqual(result["expires_in"], 3600)

        # Vérifier que le client partagé a été créé
        client = get_shared_client()
        self.assertIsNotNone(client)
        self.assertEqual(client._token, "token_xyz789")

    @patch.object(ArzekaPayment, "initiate_payment")
    @patch("arzeka.requests.Session.post")
    def test_initiate_payment_function(self, mock_post, mock_initiate):
        """Test de la fonction initiate_payment"""
        # D'abord authentifier
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        authenticate("user", "pass")

        # Mock de initiate_payment
        mock_initiate.return_value = {"status": "success", "mappedOrderId": "ORDER123"}

        payment_data = {
            "amount": 1000,
            "merchant_id": "TEST123",
            "additional_info": {
                "first_name": "John",
                "last_name": "Doe",
                "mobile": "70123456",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        result = initiate_payment(payment_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["mappedOrderId"], "ORDER123")
        mock_initiate.assert_called_once()

    @patch.object(ArzekaPayment, "check_payment")
    @patch("arzeka.requests.Session.post")
    def test_check_payment_function(self, mock_post, mock_check):
        """Test de la fonction check_payment"""
        # D'abord authentifier
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_456",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        authenticate("user", "pass")

        # Mock de check_payment
        mock_check.return_value = {
            "status": "completed",
            "mappedOrderId": "ORDER456",
            "amount": 2000,
        }

        result = check_payment("ORDER456")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mappedOrderId"], "ORDER456")
        mock_check.assert_called_once_with("ORDER456", None)

    def test_initiate_payment_not_authenticated(self):
        """Test initiate_payment sans authentification"""
        payment_data = {
            "amount": 1000,
            "merchant_id": "TEST123",
            "additional_info": {
                "first_name": "John",
                "last_name": "Doe",
                "mobile": "70123456",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        with self.assertRaises(ArzekaAuthenticationError):
            initiate_payment(payment_data)

    def test_check_payment_not_authenticated(self):
        """Test check_payment sans authentification"""
        with self.assertRaises(ArzekaAuthenticationError):
            check_payment("ORDER123")

    @patch("arzeka.requests.Session.post")
    def test_get_shared_client(self, mock_post):
        """Test de récupération du client partagé"""
        # Avant authentification
        self.assertIsNone(get_shared_client())

        # Après authentification
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_shared",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        authenticate("user", "pass")

        client = get_shared_client()
        self.assertIsNotNone(client)
        self.assertIsInstance(client, ArzekaPayment)
        self.assertEqual(client._token, "token_shared")

    @patch("arzeka.requests.Session.post")
    def test_close_shared_client(self, mock_post):
        """Test de fermeture du client partagé"""
        # Créer un client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_close",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        authenticate("user", "pass")
        self.assertIsNotNone(get_shared_client())

        # Fermer le client
        close_shared_client()
        self.assertIsNone(get_shared_client())

        # Appeler close à nouveau ne devrait pas causer d'erreur
        close_shared_client()


class TestIntegrationScenarios(unittest.TestCase):
    """Tests de scénarios d'intégration"""

    def setUp(self):
        """Configuration avant chaque test"""
        close_shared_client()

    def tearDown(self):
        """Nettoyage après chaque test"""
        close_shared_client()

    @patch("arzeka.requests.Session.post")
    def test_full_payment_flow(self, mock_post):
        """Test du flux complet de paiement"""
        # 1. Authentification
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "access_token": "flow_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        auth_response.raise_for_status = Mock()

        # 2. Initiation du paiement
        payment_response = Mock()
        payment_response.status_code = 200
        payment_response.json.return_value = {
            "status": "pending",
            "mappedOrderId": "FLOW123",
            "paymentUrl": "https://pay.example.com/FLOW123",
        }
        payment_response.raise_for_status = Mock()

        # 3. Vérification du paiement
        check_response = Mock()
        check_response.status_code = 200
        check_response.json.return_value = {
            "status": "completed",
            "mappedOrderId": "FLOW123",
            "amount": 1500,
        }
        check_response.raise_for_status = Mock()

        mock_post.side_effect = [auth_response, payment_response, check_response]

        # Exécuter le flux
        client = ArzekaPayment()

        # Authentification
        auth_result = client.authenticate("user", "pass")
        self.assertEqual(auth_result["access_token"], "flow_token")

        # Initiation
        payment_data = {
            "amount": 1500,
            "merchant_id": "MERCHANT_FLOW",
            "additional_info": {
                "first_name": "Test",
                "last_name": "User",
                "mobile": "70111111",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }
        payment_result = client.initiate_payment(**payment_data)
        self.assertEqual(payment_result["status"], "pending")

        # Vérification
        check_result = client.check_payment("FLOW123")
        self.assertEqual(check_result["status"], "completed")

        client.close()

    @patch("arzeka.requests.Session.post")
    @patch.object(ArzekaPayment, "authenticate")
    def test_auto_reauth_on_expired_token(self, mock_auth, mock_post):
        """Test de réauthentification automatique"""
        client = ArzekaPayment()

        # Simuler une authentification initiale
        client._token = "expired_token"
        client._expires_at = time.time() - 100  # Expiré
        client._username = "user"
        client._password = "pass"

        # Mock de la réauthentification
        def reauth(username, password):
            client._token = "new_token"
            client._expires_at = time.time() + 3600
            return {
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }

        mock_auth.side_effect = reauth

        # Mock de la requête de paiement
        payment_response = Mock()
        payment_response.status_code = 200
        payment_response.json.return_value = {
            "status": "success",
            "mappedOrderId": "AUTO123",
        }
        payment_response.raise_for_status = Mock()
        mock_post.return_value = payment_response

        # Faire une requête qui devrait déclencher la réauthentification
        payment_data = {
            "amount": 1000,
            "merchant_id": "TEST",
            "additional_info": {
                "first_name": "John",
                "last_name": "Doe",
                "mobile": "70123456",
            },
            "hash_secret": "secret",
            "link_for_update_status": "https://example.com/webhook",
            "link_back_to_calling_website": "https://example.com/return",
        }

        result = client.initiate_payment(**payment_data)

        # Vérifier que la réauthentification a été appelée
        mock_auth.assert_called_once_with("user", "pass")
        self.assertEqual(client._token, "new_token")
        self.assertEqual(result["status"], "success")

        client.close()


if __name__ == "__main__":
    unittest.main()
