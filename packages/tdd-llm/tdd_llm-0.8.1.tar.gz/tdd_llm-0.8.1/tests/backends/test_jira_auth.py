"""Tests for Jira OAuth authentication."""

import json
import time
from unittest import mock

import pytest

from tdd_llm.config import JiraConfig


class TestTokenEncryption:
    """Tests for TokenEncryption class."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption/decryption preserves data."""
        from tdd_llm.backends.jira.auth import TokenEncryption

        encryption = TokenEncryption()
        data = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_at": 1234567890.0,
        }

        encrypted = encryption.encrypt(data)
        assert encrypted != json.dumps(data)  # Should be different

        decrypted = encryption.decrypt(encrypted)
        assert decrypted == data

    def test_encryption_is_deterministic_for_same_machine(self):
        """Test that same data encrypts consistently on same machine."""
        from tdd_llm.backends.jira.auth import TokenEncryption

        enc1 = TokenEncryption()
        enc2 = TokenEncryption()

        data = {"test": "value"}

        # Both should be able to decrypt each other's data
        encrypted1 = enc1.encrypt(data)
        decrypted2 = enc2.decrypt(encrypted1)
        assert decrypted2 == data

    def test_decrypt_invalid_data_raises_error(self):
        """Test that decrypting invalid data raises OAuthTokenError."""
        from tdd_llm.backends.jira.auth import OAuthTokenError, TokenEncryption

        encryption = TokenEncryption()

        with pytest.raises(OAuthTokenError, match="Failed to decrypt"):
            encryption.decrypt("invalid-encrypted-data")


class TestOAuthTokens:
    """Tests for OAuthTokens dataclass."""

    def test_is_expired_when_past_expiry(self):
        """Test that tokens are marked expired after expiry time."""
        from tdd_llm.backends.jira.auth import OAuthTokens

        tokens = OAuthTokens(
            access_token="test",
            refresh_token="test",
            expires_at=time.time() - 100,  # Expired 100 seconds ago
            cloud_id="cloud-123",
            site_url="https://test.atlassian.net",
        )

        assert tokens.is_expired() is True

    def test_is_expired_with_buffer(self):
        """Test that tokens are marked expired within buffer time."""
        from tdd_llm.backends.jira.auth import TOKEN_EXPIRY_BUFFER, OAuthTokens

        tokens = OAuthTokens(
            access_token="test",
            refresh_token="test",
            expires_at=time.time() + TOKEN_EXPIRY_BUFFER - 10,  # Within buffer
            cloud_id="cloud-123",
            site_url="https://test.atlassian.net",
        )

        assert tokens.is_expired() is True

    def test_is_not_expired_when_valid(self):
        """Test that valid tokens are not marked expired."""
        from tdd_llm.backends.jira.auth import OAuthTokens

        tokens = OAuthTokens(
            access_token="test",
            refresh_token="test",
            expires_at=time.time() + 3600,  # Expires in 1 hour
            cloud_id="cloud-123",
            site_url="https://test.atlassian.net",
        )

        assert tokens.is_expired() is False

    def test_to_dict_and_from_dict(self):
        """Test serialization roundtrip."""
        from tdd_llm.backends.jira.auth import OAuthTokens

        original = OAuthTokens(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_at=1234567890.0,
            cloud_id="cloud-789",
            site_url="https://test.atlassian.net",
        )

        data = original.to_dict()
        restored = OAuthTokens.from_dict(data)

        assert restored.access_token == original.access_token
        assert restored.refresh_token == original.refresh_token
        assert restored.expires_at == original.expires_at
        assert restored.cloud_id == original.cloud_id
        assert restored.site_url == original.site_url


class TestTokenStorage:
    """Tests for TokenStorage class."""

    def test_save_and_load_tokens(self, tmp_path):
        """Test saving and loading tokens."""
        from tdd_llm.backends.jira.auth import OAuthTokens, TokenStorage

        storage = TokenStorage(config_dir=tmp_path)

        tokens = OAuthTokens(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_at=time.time() + 3600,
            cloud_id="cloud-789",
            site_url="https://test.atlassian.net",
        )

        storage.save_tokens(tokens)
        assert storage.token_path.exists()

        loaded = storage.load_tokens()
        assert loaded is not None
        assert loaded.access_token == tokens.access_token
        assert loaded.refresh_token == tokens.refresh_token
        assert loaded.cloud_id == tokens.cloud_id

    def test_load_returns_none_when_no_file(self, tmp_path):
        """Test that load returns None when no token file exists."""
        from tdd_llm.backends.jira.auth import TokenStorage

        storage = TokenStorage(config_dir=tmp_path)
        assert storage.load_tokens() is None

    def test_delete_tokens(self, tmp_path):
        """Test deleting stored tokens."""
        from tdd_llm.backends.jira.auth import OAuthTokens, TokenStorage

        storage = TokenStorage(config_dir=tmp_path)

        tokens = OAuthTokens(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_at=time.time() + 3600,
            cloud_id="cloud-789",
            site_url="https://test.atlassian.net",
        )

        storage.save_tokens(tokens)
        assert storage.token_path.exists()

        storage.delete_tokens()
        assert not storage.token_path.exists()
        assert storage.load_tokens() is None


class TestJiraOAuthFlow:
    """Tests for JiraOAuthFlow class."""

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        from tdd_llm.backends.jira.auth import JiraOAuthFlow

        flow = JiraOAuthFlow(client_id="test-client-id", client_secret="test-secret")
        redirect_uri = "http://localhost:8089/callback"
        state = "test-state-123"

        url = flow.get_authorization_url(redirect_uri, state)

        assert "auth.atlassian.com/authorize" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http" in url
        assert "state=test-state-123" in url
        assert "response_type=code" in url
        assert "offline_access" in url  # Required scope

    @mock.patch("httpx.Client")
    def test_exchange_code_for_tokens(self, mock_client_class):
        """Test token exchange with mocked API."""
        from tdd_llm.backends.jira.auth import JiraOAuthFlow

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }

        mock_client = mock.Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = mock.Mock(return_value=mock_client)
        mock_client.__exit__ = mock.Mock(return_value=False)
        mock_client_class.return_value = mock_client

        flow = JiraOAuthFlow(client_id="test-client", client_secret="test-secret")
        access_token, refresh_token, expires_in = flow.exchange_code_for_tokens(
            code="auth-code",
            redirect_uri="http://localhost:8089/callback",
        )

        assert access_token == "new-access-token"
        assert refresh_token == "new-refresh-token"
        assert expires_in == 3600

    @mock.patch("httpx.Client")
    def test_refresh_access_token(self, mock_client_class):
        """Test token refresh with mocked API."""
        from tdd_llm.backends.jira.auth import JiraOAuthFlow

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }

        mock_client = mock.Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = mock.Mock(return_value=mock_client)
        mock_client.__exit__ = mock.Mock(return_value=False)
        mock_client_class.return_value = mock_client

        flow = JiraOAuthFlow(client_id="test-client", client_secret="test-secret")
        access_token, refresh_token, expires_in = flow.refresh_access_token(
            refresh_token="old-refresh-token"
        )

        assert access_token == "refreshed-access-token"
        assert refresh_token == "new-refresh-token"


class TestJiraAuthManager:
    """Tests for JiraAuthManager class."""

    @pytest.fixture
    def oauth_config(self, monkeypatch):
        """Create a config with OAuth credentials."""
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_SECRET", "test-client-secret")
        return JiraConfig()

    @pytest.fixture
    def api_token_config(self, monkeypatch):
        """Create a config with API token."""
        monkeypatch.setenv("JIRA_API_TOKEN", "test-api-token")
        return JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
        )

    def test_is_oauth_available(self, oauth_config):
        """Test OAuth availability check."""
        from tdd_llm.backends.jira.auth import JiraAuthManager

        auth = JiraAuthManager(oauth_config)
        assert auth.is_oauth_available() is True

    def test_is_oauth_not_available_without_credentials(self, tmp_path):
        """Test OAuth not available without credentials."""
        from tdd_llm.backends.jira.auth import JiraAuthManager, TokenStorage

        config = JiraConfig()
        # Use a temp storage to ensure no existing credentials are found
        storage = TokenStorage(config_dir=tmp_path)
        auth = JiraAuthManager(config, storage=storage)
        assert auth.is_oauth_available() is False

    def test_get_auth_header_basic_auth(self, api_token_config, tmp_path):
        """Test Basic auth header generation."""
        from tdd_llm.backends.jira.auth import JiraAuthManager, TokenStorage

        storage = TokenStorage(config_dir=tmp_path)  # No tokens stored
        auth = JiraAuthManager(api_token_config, storage=storage)

        header = auth.get_auth_header()
        assert "Authorization" in header
        assert header["Authorization"].startswith("Basic ")

    def test_get_auth_header_oauth(self, oauth_config, tmp_path):
        """Test OAuth Bearer header generation."""
        from tdd_llm.backends.jira.auth import (
            JiraAuthManager,
            OAuthTokens,
            TokenStorage,
        )

        storage = TokenStorage(config_dir=tmp_path)

        # Store valid tokens
        tokens = OAuthTokens(
            access_token="oauth-access-token",
            refresh_token="oauth-refresh-token",
            expires_at=time.time() + 3600,
            cloud_id="cloud-123",
            site_url="https://test.atlassian.net",
        )
        storage.save_tokens(tokens)

        auth = JiraAuthManager(oauth_config, storage=storage)
        header = auth.get_auth_header()

        assert "Authorization" in header
        assert header["Authorization"] == "Bearer oauth-access-token"

    def test_status_with_oauth(self, oauth_config, tmp_path):
        """Test status reporting with OAuth tokens."""
        from tdd_llm.backends.jira.auth import (
            JiraAuthManager,
            OAuthTokens,
            TokenStorage,
        )

        storage = TokenStorage(config_dir=tmp_path)

        tokens = OAuthTokens(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_at=time.time() + 3600,
            cloud_id="cloud-789",
            site_url="https://test.atlassian.net",
        )
        storage.save_tokens(tokens)

        auth = JiraAuthManager(oauth_config, storage=storage)
        status = auth.status()

        assert status["method"] == "oauth"
        assert status["authenticated"] is True
        assert status["site_url"] == "https://test.atlassian.net"
        assert status["is_expired"] is False

    def test_status_with_api_token(self, api_token_config, tmp_path):
        """Test status reporting with API token."""
        from tdd_llm.backends.jira.auth import JiraAuthManager, TokenStorage

        storage = TokenStorage(config_dir=tmp_path)  # No OAuth tokens
        auth = JiraAuthManager(api_token_config, storage=storage)
        status = auth.status()

        assert status["method"] == "api_token"
        assert status["authenticated"] is True
        assert status["base_url"] == "https://test.atlassian.net"

    def test_status_not_authenticated(self, tmp_path):
        """Test status when not authenticated."""
        from tdd_llm.backends.jira.auth import JiraAuthManager, TokenStorage

        config = JiraConfig()  # No OAuth or API token
        storage = TokenStorage(config_dir=tmp_path)
        auth = JiraAuthManager(config, storage=storage)
        status = auth.status()

        assert status["method"] is None
        assert status["authenticated"] is False

    def test_logout(self, oauth_config, tmp_path):
        """Test logout removes tokens."""
        from tdd_llm.backends.jira.auth import (
            JiraAuthManager,
            OAuthTokens,
            TokenStorage,
        )

        storage = TokenStorage(config_dir=tmp_path)

        tokens = OAuthTokens(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_at=time.time() + 3600,
            cloud_id="cloud-789",
            site_url="https://test.atlassian.net",
        )
        storage.save_tokens(tokens)

        auth = JiraAuthManager(oauth_config, storage=storage)
        assert auth.has_valid_tokens() is True

        auth.logout()
        assert auth.has_valid_tokens() is False
        assert storage.load_tokens() is None


class TestOAuthCallbackServer:
    """Tests for OAuthCallbackServer."""

    def test_redirect_uri_format(self):
        """Test redirect URI format."""
        from tdd_llm.backends.jira.auth import OAuthCallbackServer

        server = OAuthCallbackServer(port=8089)
        assert server.redirect_uri == "http://localhost:8089/callback"

    def test_server_starts_and_stops(self):
        """Test that server can start and stop without errors."""
        from tdd_llm.backends.jira.auth import OAuthCallbackServer

        server = OAuthCallbackServer(port=18089)  # Use unusual port to avoid conflicts
        server.start()

        # Should be able to stop without error
        server.stop()


class TestConfigOAuthFields:
    """Tests for OAuth fields in JiraConfig."""

    def test_effective_oauth_client_id_from_env(self, monkeypatch):
        """Test OAuth client ID from environment variable."""
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_ID", "env-client-id")
        config = JiraConfig(oauth_client_id="config-client-id")
        assert config.effective_oauth_client_id == "env-client-id"

    def test_effective_oauth_client_id_from_config(self):
        """Test OAuth client ID from config when env not set."""
        config = JiraConfig(oauth_client_id="config-client-id")
        assert config.effective_oauth_client_id == "config-client-id"

    def test_effective_oauth_client_secret_from_env(self, monkeypatch):
        """Test OAuth client secret from environment variable."""
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_SECRET", "env-secret")
        config = JiraConfig()
        assert config.effective_oauth_client_secret == "env-secret"

    def test_is_oauth_configured(self, monkeypatch):
        """Test OAuth configuration check."""
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_ID", "client-id")
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_SECRET", "client-secret")
        config = JiraConfig()
        assert config.is_oauth_configured() is True

    def test_is_oauth_not_configured_without_secret(self, monkeypatch):
        """Test OAuth not configured without secret."""
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_ID", "client-id")
        config = JiraConfig()
        assert config.is_oauth_configured() is False

    def test_is_configured_with_oauth(self, monkeypatch):
        """Test is_configured returns True with OAuth."""
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_ID", "client-id")
        monkeypatch.setenv("JIRA_OAUTH_CLIENT_SECRET", "client-secret")
        config = JiraConfig()
        assert config.is_configured() is True

    def test_is_configured_with_api_token(self, monkeypatch):
        """Test is_configured returns True with API token."""
        monkeypatch.setenv("JIRA_API_TOKEN", "api-token")
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
        )
        assert config.is_configured() is True
