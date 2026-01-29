import time
import unittest
from unittest.mock import Mock, patch

import requests

from fasoarzeka import (
    ArzekaAuthenticationError,
    ArzekaPayment,
    ArzekaValidationError,
    authenticate,
    check_payment,
    close_shared_client,
    get_shared_client,
    initiate_payment,
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

    @patch("fasoarzeka.base.requests.Session.post")
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

    @patch("fasoarzeka.base.requests.Session.post")
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

    @patch("fasoarzeka.base.requests.Session.post")
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


if __name__ == "__main__":
    unittest.main()
