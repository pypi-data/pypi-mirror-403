"""OAuth 2.0 authentication for Jira Cloud.

This module provides OAuth 2.0 authentication with encrypted token storage.
Tokens are encrypted using Fernet symmetric encryption with a machine-derived key.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import secrets
import socket
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .client import JiraConfig

# Lazy import cryptography to allow graceful error if not installed
try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore

from ...paths import get_config_dir

# OAuth constants for Atlassian
ATLASSIAN_AUTH_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

# Scopes required for tdd-llm operations
OAUTH_SCOPES = [
    "read:jira-work",
    "write:jira-work",
    "read:jira-user",
    "offline_access",  # Required for refresh tokens
]

DEFAULT_CALLBACK_PORT = 8089
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes buffer before expiry


class OAuthError(Exception):
    """Base OAuth error."""

    pass


class OAuthConfigurationError(OAuthError):
    """OAuth not properly configured."""

    pass


class OAuthTokenError(OAuthError):
    """Token-related error (expired, invalid, etc.)."""

    pass


class OAuthCallbackError(OAuthError):
    """Error during OAuth callback."""

    pass


def _check_cryptography() -> None:
    """Check that cryptography is installed."""
    if Fernet is None:
        raise OAuthError(
            "cryptography package is required for OAuth. Install with: pip install cryptography"
        )


class TokenEncryption:
    """Encrypt/decrypt tokens using machine-derived key.

    The encryption key is derived from machine-specific identifiers
    (hostname + platform) to ensure tokens are tied to this machine.
    """

    def __init__(self) -> None:
        """Initialize encryption with machine-derived key."""
        _check_cryptography()
        self._fernet = Fernet(self._derive_key())

    def _derive_key(self) -> bytes:
        """Derive a Fernet key from machine identifiers.

        Returns:
            32-byte base64-encoded key for Fernet.
        """
        # Combine machine-specific identifiers
        machine_id = f"{socket.gethostname()}:{platform.system()}:{platform.machine()}"

        # Add a static salt (not secret, just for key derivation consistency)
        salt = b"tdd-llm-jira-oauth-v1"

        # Derive 32-byte key using SHA256
        key_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            machine_id.encode(),
            salt,
            iterations=100000,
        )

        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(key_bytes)

    def encrypt(self, data: dict) -> str:
        """Encrypt token data to base64 string.

        Args:
            data: Dictionary containing token data.

        Returns:
            Base64-encoded encrypted string.
        """
        json_bytes = json.dumps(data).encode("utf-8")
        encrypted = self._fernet.encrypt(json_bytes)
        return encrypted.decode("utf-8")

    def decrypt(self, encrypted: str) -> dict:
        """Decrypt base64 string to token data.

        Args:
            encrypted: Base64-encoded encrypted string.

        Returns:
            Decrypted dictionary.

        Raises:
            OAuthTokenError: If decryption fails (wrong machine, corrupted data).
        """
        try:
            decrypted = self._fernet.decrypt(encrypted.encode("utf-8"))
            return json.loads(decrypted.decode("utf-8"))
        except InvalidToken as e:
            raise OAuthTokenError(
                "Failed to decrypt tokens. This may happen if tokens were "
                "created on a different machine. Please run 'tdd-llm jira login' again."
            ) from e
        except json.JSONDecodeError as e:
            raise OAuthTokenError(f"Corrupted token data: {e}") from e


@dataclass
class OAuthCredentials:
    """OAuth client credentials (stored encrypted)."""

    client_id: str
    client_secret: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

    @classmethod
    def from_dict(cls, data: dict) -> OAuthCredentials:
        """Create from dictionary."""
        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
        )


@dataclass
class OAuthTokens:
    """OAuth token storage."""

    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp
    cloud_id: str  # Atlassian cloud instance ID
    site_url: str  # e.g., "https://company.atlassian.net"

    def is_expired(self) -> bool:
        """Check if access token is expired (with buffer).

        Returns:
            True if token is expired or will expire within buffer time.
        """
        return time.time() >= (self.expires_at - TOKEN_EXPIRY_BUFFER)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "cloud_id": self.cloud_id,
            "site_url": self.site_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> OAuthTokens:
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["expires_at"],
            cloud_id=data["cloud_id"],
            site_url=data["site_url"],
        )


class TokenStorage:
    """Manage encrypted token and credential storage in config directory."""

    TOKEN_FILE = "jira_oauth_tokens.enc"
    CREDENTIALS_FILE = "jira_oauth_credentials.enc"

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize storage.

        Args:
            config_dir: Directory to store tokens. Defaults to user config dir.
        """
        self.config_dir = config_dir or get_config_dir()
        self._encryption: TokenEncryption | None = None

    @property
    def token_path(self) -> Path:
        """Get path to token file."""
        return self.config_dir / self.TOKEN_FILE

    @property
    def credentials_path(self) -> Path:
        """Get path to credentials file."""
        return self.config_dir / self.CREDENTIALS_FILE

    def _get_encryption(self) -> TokenEncryption:
        """Lazy-load encryption handler."""
        if self._encryption is None:
            self._encryption = TokenEncryption()
        return self._encryption

    def save_tokens(self, tokens: OAuthTokens) -> None:
        """Save encrypted tokens to disk.

        Args:
            tokens: OAuth tokens to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        encrypted = self._get_encryption().encrypt(tokens.to_dict())

        # Write with restrictive permissions
        self.token_path.write_text(encrypted, encoding="utf-8")

        # Set restrictive permissions on Unix
        if os.name != "nt":
            os.chmod(self.token_path, 0o600)

    def load_tokens(self) -> OAuthTokens | None:
        """Load and decrypt tokens from disk.

        Returns:
            OAuth tokens if file exists and is valid, None otherwise.
        """
        if not self.token_path.exists():
            return None

        try:
            encrypted = self.token_path.read_text(encoding="utf-8")
            data = self._get_encryption().decrypt(encrypted)
            return OAuthTokens.from_dict(data)
        except (OAuthTokenError, KeyError):
            # Invalid or corrupted tokens
            return None

    def delete_tokens(self) -> None:
        """Delete stored tokens."""
        if self.token_path.exists():
            self.token_path.unlink()

    def save_credentials(self, credentials: OAuthCredentials) -> None:
        """Save encrypted OAuth credentials to disk.

        Args:
            credentials: OAuth client credentials to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        encrypted = self._get_encryption().encrypt(credentials.to_dict())

        # Write with restrictive permissions
        self.credentials_path.write_text(encrypted, encoding="utf-8")

        # Set restrictive permissions on Unix
        if os.name != "nt":
            os.chmod(self.credentials_path, 0o600)

    def load_credentials(self) -> OAuthCredentials | None:
        """Load and decrypt OAuth credentials from disk.

        Returns:
            OAuth credentials if file exists and is valid, None otherwise.
        """
        if not self.credentials_path.exists():
            return None

        try:
            encrypted = self.credentials_path.read_text(encoding="utf-8")
            data = self._get_encryption().decrypt(encrypted)
            return OAuthCredentials.from_dict(data)
        except (OAuthTokenError, KeyError):
            # Invalid or corrupted credentials
            return None

    def delete_credentials(self) -> None:
        """Delete stored credentials."""
        if self.credentials_path.exists():
            self.credentials_path.unlink()

    def delete_all(self) -> None:
        """Delete all stored OAuth data (tokens and credentials)."""
        self.delete_tokens()
        self.delete_credentials()


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress HTTP server logs."""
        pass

    def do_GET(self) -> None:
        """Handle GET request with authorization code."""
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if "code" in query:
            self.server.auth_code = query["code"][0]  # type: ignore
            self.server.auth_state = query.get("state", [None])[0]  # type: ignore
            self._send_success_response()
        elif "error" in query:
            self.server.auth_error = query.get("error_description", query["error"])[0]  # type: ignore
            self._send_error_response(self.server.auth_error)  # type: ignore
        else:
            self._send_error_response("Invalid callback request")

    def _send_success_response(self) -> None:
        """Send success HTML response."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Authorization Successful</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Authorization Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def _send_error_response(self, error: str) -> None:
        """Send error HTML response."""
        self.send_response(400)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authorization Failed</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Authorization Failed</h1>
            <p>Error: {error}</p>
            <p>Please try again.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())


class OAuthCallbackServer:
    """Temporary HTTP server to receive OAuth callback."""

    def __init__(self, port: int = DEFAULT_CALLBACK_PORT) -> None:
        """Initialize callback server.

        Args:
            port: Port to listen on.
        """
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def redirect_uri(self) -> str:
        """Get the redirect URI for this server."""
        return f"http://localhost:{self.port}/callback"

    def start(self) -> None:
        """Start the callback server in a background thread."""
        self._server = HTTPServer(("localhost", self.port), _OAuthCallbackHandler)
        self._server.auth_code = None  # type: ignore
        self._server.auth_state = None  # type: ignore
        self._server.auth_error = None  # type: ignore

        self._thread = threading.Thread(target=self._server.handle_request)
        self._thread.daemon = True
        self._thread.start()

    def wait_for_callback(self, timeout: int = 300) -> str:
        """Wait for callback and return authorization code.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            Authorization code from callback.

        Raises:
            OAuthCallbackError: If callback fails or times out.
        """
        if self._thread is None:
            raise OAuthCallbackError("Server not started")

        self._thread.join(timeout=timeout)

        if self._thread.is_alive():
            raise OAuthCallbackError(
                f"Authorization timed out after {timeout} seconds. "
                "Please try again and complete authorization in your browser."
            )

        if self._server.auth_error:  # type: ignore
            raise OAuthCallbackError(f"Authorization failed: {self._server.auth_error}")  # type: ignore

        if not self._server.auth_code:  # type: ignore
            raise OAuthCallbackError("No authorization code received")

        return self._server.auth_code  # type: ignore

    def get_state(self) -> str | None:
        """Get the state parameter from callback."""
        if self._server:
            return self._server.auth_state  # type: ignore
        return None

    def stop(self) -> None:
        """Stop the callback server."""
        if self._server:
            self._server.server_close()


class JiraOAuthFlow:
    """Handle complete OAuth 2.0 flow for Jira."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        """Initialize OAuth flow.

        Args:
            client_id: OAuth client ID from Atlassian Developer Console.
            client_secret: OAuth client secret.
        """
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate authorization URL for user to visit.

        Args:
            redirect_uri: Callback URL.
            state: CSRF protection state value.

        Returns:
            URL to redirect user to for authorization.
        """
        params = {
            "audience": "api.atlassian.com",
            "client_id": self.client_id,
            "scope": " ".join(OAUTH_SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
        return f"{ATLASSIAN_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> tuple[str, str, int]:
        """Exchange authorization code for access/refresh tokens.

        Args:
            code: Authorization code from callback.
            redirect_uri: Same redirect URI used in authorization.

        Returns:
            Tuple of (access_token, refresh_token, expires_in_seconds).

        Raises:
            OAuthError: If token exchange fails.
        """
        with httpx.Client() as client:
            response = client.post(
                ATLASSIAN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )

            if response.status_code != 200:
                error = response.json().get("error_description", response.text)
                raise OAuthError(f"Token exchange failed: {error}")

            data = response.json()
            return (
                data["access_token"],
                data["refresh_token"],
                data.get("expires_in", 3600),
            )

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str, int]:
        """Refresh expired access token.

        Args:
            refresh_token: Current refresh token.

        Returns:
            Tuple of (new_access_token, new_refresh_token, expires_in_seconds).

        Raises:
            OAuthTokenError: If refresh fails (token expired or revoked).
        """
        with httpx.Client() as client:
            response = client.post(
                ATLASSIAN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )

            if response.status_code != 200:
                error = response.json().get("error_description", response.text)
                raise OAuthTokenError(
                    f"Token refresh failed: {error}. Please run 'tdd-llm jira login' again."
                )

            data = response.json()
            return (
                data["access_token"],
                data.get("refresh_token", refresh_token),  # May not always be returned
                data.get("expires_in", 3600),
            )

    def get_accessible_resources(self, access_token: str) -> list[dict]:
        """Get list of Atlassian sites accessible with this token.

        Args:
            access_token: Valid access token.

        Returns:
            List of accessible resources with 'id', 'url', 'name' keys.
        """
        with httpx.Client() as client:
            response = client.get(
                ATLASSIAN_RESOURCES_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get accessible resources: {response.text}")

            return response.json()


class JiraAuthManager:
    """High-level auth manager used by JiraClient."""

    def __init__(
        self,
        config: JiraConfig,
        storage: TokenStorage | None = None,
    ) -> None:
        """Initialize auth manager.

        Args:
            config: Jira configuration.
            storage: Token storage (defaults to standard location).
        """
        self.config = config
        self.storage = storage or TokenStorage()
        self._cached_tokens: OAuthTokens | None = None

    def _get_credentials(self) -> OAuthCredentials | None:
        """Get OAuth credentials from storage or environment.

        Priority: stored credentials > environment variables > config file.
        """
        # First try stored credentials
        stored = self.storage.load_credentials()
        if stored:
            return stored

        # Then try environment variables / config
        client_id = self.config.effective_oauth_client_id
        client_secret = self.config.effective_oauth_client_secret

        if client_id and client_secret:
            return OAuthCredentials(client_id=client_id, client_secret=client_secret)

        return None

    def _get_oauth_flow(self) -> JiraOAuthFlow:
        """Get OAuth flow handler."""
        credentials = self._get_credentials()

        if not credentials:
            raise OAuthConfigurationError(
                "OAuth not configured. Run 'tdd-llm jira login' to authenticate."
            )

        return JiraOAuthFlow(credentials.client_id, credentials.client_secret)

    def is_oauth_available(self) -> bool:
        """Check if OAuth credentials are configured (stored or env vars)."""
        return self._get_credentials() is not None

    def has_valid_tokens(self) -> bool:
        """Check if valid OAuth tokens are stored."""
        tokens = self.storage.load_tokens()
        return tokens is not None

    def get_tokens(self) -> OAuthTokens | None:
        """Get current tokens, loading from storage if needed."""
        if self._cached_tokens is None:
            self._cached_tokens = self.storage.load_tokens()
        return self._cached_tokens

    def ensure_valid_token(self, force_refresh: bool = False) -> str:
        """Ensure we have a valid access token, refreshing if needed.

        Args:
            force_refresh: Force token refresh even if not expired.

        Returns:
            Valid access token.

        Raises:
            OAuthTokenError: If no valid token available.
        """
        tokens = self.get_tokens()

        if tokens is None:
            raise OAuthTokenError("Not authenticated. Run 'tdd-llm jira login' first.")

        if force_refresh or tokens.is_expired():
            # Refresh the token
            oauth_flow = self._get_oauth_flow()
            access_token, refresh_token, expires_in = oauth_flow.refresh_access_token(
                tokens.refresh_token
            )

            # Update tokens
            tokens = OAuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=time.time() + expires_in,
                cloud_id=tokens.cloud_id,
                site_url=tokens.site_url,
            )
            self.storage.save_tokens(tokens)
            self._cached_tokens = tokens

        return tokens.access_token

    def get_auth_header(self) -> dict[str, str]:
        """Get authorization header for API requests.

        Returns Bearer token if OAuth tokens are available,
        falls back to Basic auth if API token is set.

        Returns:
            Authorization header dict.

        Raises:
            OAuthConfigurationError: If no auth method is configured.
        """
        tokens = self.get_tokens()

        if tokens is not None:
            # Use OAuth Bearer token
            access_token = self.ensure_valid_token()
            return {"Authorization": f"Bearer {access_token}"}

        # Fall back to Basic auth
        if self.config.api_token and self.config.effective_email:
            import base64

            credentials = f"{self.config.effective_email}:{self.config.api_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}

        raise OAuthConfigurationError(
            "No authentication configured. Either:\n"
            "  - Run 'tdd-llm jira login' for OAuth authentication\n"
            "  - Set JIRA_API_TOKEN environment variable for API token auth"
        )

    def get_base_url(self) -> str:
        """Get the appropriate base URL for API requests.

        Returns:
            Base URL for Jira API.

        Raises:
            OAuthConfigurationError: If not configured.
        """
        tokens = self.get_tokens()

        if tokens is not None:
            # OAuth uses cloud ID-based URL
            return f"https://api.atlassian.com/ex/jira/{tokens.cloud_id}"

        # Basic auth uses direct instance URL
        if self.config.effective_base_url:
            return self.config.effective_base_url.rstrip("/")

        raise OAuthConfigurationError("No Jira base URL configured.")

    def login(
        self,
        port: int = DEFAULT_CALLBACK_PORT,
        open_browser: bool = True,
        timeout: int = 300,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> OAuthTokens:
        """Perform interactive OAuth login flow.

        Args:
            port: Port for callback server.
            open_browser: Whether to auto-open browser.
            timeout: Seconds to wait for callback.
            client_id: OAuth client ID (if not already stored/configured).
            client_secret: OAuth client secret (if not already stored/configured).

        Returns:
            OAuth tokens after successful authentication.
        """
        # If credentials provided, store them first
        if client_id and client_secret:
            credentials = OAuthCredentials(client_id=client_id, client_secret=client_secret)
            self.storage.save_credentials(credentials)

        oauth_flow = self._get_oauth_flow()
        callback_server = OAuthCallbackServer(port)

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Start callback server
        callback_server.start()

        try:
            # Generate and open authorization URL
            auth_url = oauth_flow.get_authorization_url(callback_server.redirect_uri, state)

            if open_browser:
                webbrowser.open(auth_url)
            else:
                print(f"\nOpen this URL in your browser:\n{auth_url}\n")

            # Wait for callback
            code = callback_server.wait_for_callback(timeout)

            # Verify state
            received_state = callback_server.get_state()
            if received_state != state:
                raise OAuthCallbackError("State mismatch - possible CSRF attack")

            # Exchange code for tokens
            access_token, refresh_token, expires_in = oauth_flow.exchange_code_for_tokens(
                code, callback_server.redirect_uri
            )

            # Get accessible resources to find cloud ID
            resources = oauth_flow.get_accessible_resources(access_token)

            if not resources:
                raise OAuthError(
                    "No accessible Jira sites found. "
                    "Ensure your Atlassian account has access to a Jira site."
                )

            # Use first resource (could prompt if multiple)
            resource = resources[0]

            tokens = OAuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=time.time() + expires_in,
                cloud_id=resource["id"],
                site_url=resource["url"],
            )

            # Save tokens
            self.storage.save_tokens(tokens)
            self._cached_tokens = tokens

            return tokens

        finally:
            callback_server.stop()

    def logout(self) -> None:
        """Remove stored OAuth tokens."""
        self.storage.delete_tokens()
        self._cached_tokens = None

    def status(self) -> dict:
        """Get authentication status info.

        Returns:
            Dict with status information.
        """
        tokens = self.get_tokens()

        if tokens is not None:
            return {
                "method": "oauth",
                "authenticated": True,
                "site_url": tokens.site_url,
                "cloud_id": tokens.cloud_id,
                "expires_at": tokens.expires_at,
                "is_expired": tokens.is_expired(),
            }

        if self.config.api_token:
            return {
                "method": "api_token",
                "authenticated": True,
                "base_url": self.config.effective_base_url,
                "email": self.config.effective_email,
            }

        return {
            "method": None,
            "authenticated": False,
        }
