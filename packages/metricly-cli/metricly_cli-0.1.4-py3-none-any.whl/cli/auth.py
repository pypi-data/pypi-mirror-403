"""CLI Authentication - Google OAuth flow and token management.

Handles:
- Interactive OAuth login via browser
- Token storage and refresh
- User context retrieval from services layer
"""

import asyncio
import json
import secrets
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from services.auth import UserContext, get_user_by_email


class AuthenticationError(Exception):
    """Raised when authentication fails or user is not logged in."""

    pass


class CLIAuthManager:
    """Manages OAuth tokens for CLI sessions.

    Handles the complete OAuth flow:
    1. Start local callback server
    2. Open browser to Google consent screen
    3. Receive callback with auth code
    4. Exchange for tokens
    5. Store refresh token locally
    6. Look up user context from Firestore
    """

    CONFIG_DIR = Path.home() / ".metricly"
    CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    # OAuth configuration - uses same credentials as MCP server
    # Include profile scope since Google often grants it alongside email
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self):
        """Initialize the auth manager."""
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        self.CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _get_oauth_config(self) -> dict[str, Any]:
        """Get OAuth client configuration from settings."""
        from settings import get_settings

        settings = get_settings()

        if not settings.mcp_oauth_client_id or not settings.mcp_oauth_client_secret:
            raise AuthenticationError(
                "OAuth not configured. Set MCP_OAUTH_CLIENT_ID and MCP_OAUTH_CLIENT_SECRET."
            )

        return {
            "web": {
                "client_id": settings.mcp_oauth_client_id,
                "client_secret": settings.mcp_oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def _save_credentials(self, credentials: Credentials):
        """Save credentials to file with restricted permissions."""
        data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else None,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        self.CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))
        self.CREDENTIALS_FILE.chmod(0o600)

    def _load_credentials(self) -> Credentials | None:
        """Load credentials from file."""
        if not self.CREDENTIALS_FILE.exists():
            return None

        try:
            data = json.loads(self.CREDENTIALS_FILE.read_text())
            expiry = None
            if data.get("expiry"):
                expiry = datetime.fromisoformat(data["expiry"])

            return Credentials(
                token=data.get("token"),
                refresh_token=data.get("refresh_token"),
                token_uri=data.get("token_uri"),
                client_id=data.get("client_id"),
                client_secret=data.get("client_secret"),
                scopes=data.get("scopes"),
                expiry=expiry,
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def _refresh_if_needed(self, credentials: Credentials) -> Credentials:
        """Refresh credentials if expired."""
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_credentials(credentials)
        return credentials

    async def login(self) -> UserContext:
        """Interactive OAuth login flow.

        Opens browser for Google consent, then looks up user context.

        Returns:
            UserContext with user info and org context

        Raises:
            AuthenticationError: If login fails
        """
        config = self._get_oauth_config()

        # Create flow with redirect to localhost
        flow = Flow.from_client_config(
            config,
            scopes=self.SCOPES,
            redirect_uri="http://localhost:8085/callback",
        )

        # Generate authorization URL with state for CSRF protection
        state = secrets.token_urlsafe(32)
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        # Start local callback server
        auth_code = None
        received_state = None

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code, received_state
                parsed = urlparse(self.path)

                if parsed.path == "/callback":
                    params = parse_qs(parsed.query)
                    auth_code = params.get("code", [None])[0]
                    received_state = params.get("state", [None])[0]

                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h1>Login successful!</h1>"
                        b"<p>You can close this window and return to the terminal.</p>"
                        b"</body></html>"
                    )
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress server logs

        server = HTTPServer(("localhost", 8085), CallbackHandler)

        # Run server in background thread
        server_thread = Thread(target=lambda: server.handle_request())
        server_thread.start()

        # Open browser
        print(f"Opening browser for login...")
        webbrowser.open(auth_url)

        # Wait for callback
        server_thread.join(timeout=120)

        if not auth_code:
            raise AuthenticationError("Login timeout or failed to receive auth code")

        if received_state != state:
            raise AuthenticationError("Invalid state parameter - possible CSRF attack")

        # Exchange code for tokens
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials

        # Save credentials
        self._save_credentials(credentials)

        # Get user context
        return await self._get_user_context(credentials)

    async def _get_user_context(self, credentials: Credentials) -> UserContext:
        """Get user context from email in token."""
        # Get user email from Google userinfo
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            if resp.status_code != 200:
                raise AuthenticationError(f"Failed to get user info: {resp.text}")
            user_info = resp.json()

        email = user_info.get("email")
        if not email:
            raise AuthenticationError("Email not found in OAuth response")

        # Save email to config for future use
        self._save_config({"email": email})

        # Look up user context from Firestore
        try:
            return get_user_by_email(email)
        except ValueError as e:
            raise AuthenticationError(str(e))

    def _save_config(self, data: dict):
        """Save config data (non-sensitive)."""
        existing = {}
        if self.CONFIG_FILE.exists():
            try:
                existing = json.loads(self.CONFIG_FILE.read_text())
            except json.JSONDecodeError:
                pass
        existing.update(data)
        self.CONFIG_FILE.write_text(json.dumps(existing, indent=2))

    def _load_config(self) -> dict:
        """Load config data."""
        if not self.CONFIG_FILE.exists():
            return {}
        try:
            return json.loads(self.CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            return {}

    async def get_user(self) -> UserContext:
        """Get current user, refreshing token if needed.

        Returns:
            UserContext with user info and org context

        Raises:
            AuthenticationError: If not logged in or token refresh fails
        """
        credentials = self._load_credentials()
        if not credentials:
            raise AuthenticationError("Not logged in. Run 'metricly login' first.")

        if not credentials.valid:
            if credentials.refresh_token:
                try:
                    credentials = self._refresh_if_needed(credentials)
                except Exception as e:
                    raise AuthenticationError(f"Failed to refresh token: {e}")
            else:
                raise AuthenticationError(
                    "Token expired and no refresh token. Run 'metricly login' again."
                )

        return await self._get_user_context(credentials)

    async def logout(self):
        """Clear stored credentials and config."""
        if self.CREDENTIALS_FILE.exists():
            self.CREDENTIALS_FILE.unlink()
        if self.CONFIG_FILE.exists():
            self.CONFIG_FILE.unlink()

    def is_logged_in(self) -> bool:
        """Check if user has valid credentials."""
        credentials = self._load_credentials()
        if not credentials:
            return False
        if credentials.expired and not credentials.refresh_token:
            return False
        return True

    def get_stored_email(self) -> str | None:
        """Get stored email from config (doesn't validate token)."""
        config = self._load_config()
        return config.get("email")

    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if needed.

        Returns:
            Valid access token string

        Raises:
            AuthenticationError: If not logged in or token refresh fails
        """
        credentials = self._load_credentials()
        if not credentials:
            raise AuthenticationError("Not logged in. Run 'metricly login' first.")

        if not credentials.valid:
            if credentials.refresh_token:
                try:
                    credentials = self._refresh_if_needed(credentials)
                except Exception as e:
                    raise AuthenticationError(f"Failed to refresh token: {e}")
            else:
                raise AuthenticationError(
                    "Token expired and no refresh token. Run 'metricly login' again."
                )

        return credentials.token


# Global auth manager instance
auth_manager = CLIAuthManager()
