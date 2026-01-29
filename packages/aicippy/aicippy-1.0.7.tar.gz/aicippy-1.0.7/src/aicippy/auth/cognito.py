"""
AWS Cognito authentication for AiCippy.

Implements device authorization flow for CLI authentication,
with secure token storage and automatic refresh.

This module provides:
- OAuth 2.0 device/browser flow with PKCE
- Secure credential storage via OS keychain
- JWT validation against Cognito JWKS
- Automatic token refresh
- Structured error handling

Security Features:
- PKCE (Proof Key for Code Exchange) for secure auth flow
- CSRF protection via state parameter
- JWT signature verification
- Secure credential storage
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import webbrowser
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from jose import JWTError, jwt

from aicippy.auth.keychain import KeychainStorage
from aicippy.auth.models import AuthResult, TokenInfo, UserInfo
from aicippy.config import get_settings
from aicippy.exceptions import (
    AuthenticationExpiredError,
    AuthenticationInvalidError,
    AuthenticationRequiredError,
    CredentialStorageError,
    ErrorContext,
    TokenRefreshError,
)
from aicippy.utils.correlation import get_correlation_id
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import async_retry

if TYPE_CHECKING:
    from types import TracebackType

logger = get_logger(__name__)

# ============================================================================
# Constants
# ============================================================================

CALLBACK_PORT: Final[int] = 8765
CALLBACK_PATH: Final[str] = "/callback"
AUTH_TIMEOUT_SECONDS: Final[int] = 300  # 5 minutes
HTTP_TIMEOUT_SECONDS: Final[float] = 30.0
TOKEN_EXPIRY_BUFFER_SECONDS: Final[int] = 300  # Refresh 5 min before expiry


# ============================================================================
# Cognito Authentication Handler
# ============================================================================


class CognitoAuth:
    """
    AWS Cognito authentication handler.

    Supports:
    - Device/browser OAuth flow with PKCE
    - Token refresh
    - Secure credential storage
    - JWT validation

    Example:
        >>> auth = CognitoAuth()
        >>> if not auth.is_authenticated():
        ...     result = await auth.device_flow_login()
        ...     if result.success:
        ...         print(f"Logged in as {result.user_email}")
        >>> tokens = auth.get_current_tokens()
    """

    __slots__ = (
        "_settings",
        "_storage",
        "_http_client",
        "_domain",
        "_client_id",
        "_user_pool_id",
        "_region",
        "_authorize_url",
        "_token_url",
        "_userinfo_url",
        "_jwks_url",
        "_redirect_uri",
        "_jwks_cache",
    )

    def __init__(self) -> None:
        """Initialize Cognito auth handler."""
        self._settings = get_settings()
        self._storage = KeychainStorage()
        self._http_client: httpx.AsyncClient | None = None

        # Cognito endpoints
        self._domain = self._settings.cognito_domain
        self._client_id = self._settings.cognito_client_id
        self._user_pool_id = self._settings.cognito_user_pool_id
        self._region = self._settings.aws_region

        # OAuth endpoints
        self._authorize_url = f"{self._domain}/oauth2/authorize"
        self._token_url = f"{self._domain}/oauth2/token"
        self._userinfo_url = f"{self._domain}/oauth2/userInfo"
        self._jwks_url = (
            f"https://cognito-idp.{self._region}.amazonaws.com/"
            f"{self._user_pool_id}/.well-known/jwks.json"
        )

        # Callback server settings
        self._redirect_uri = f"http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"

        # JWKS cache
        self._jwks_cache: dict[str, Any] | None = None

        logger.debug(
            "cognito_auth_initialized",
            user_pool_id=self._user_pool_id,
            region=self._region,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client.

        Returns:
            Configured async HTTP client.
        """
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=HTTP_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers={
                    "User-Agent": "AiCippy-CLI/1.0",
                },
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
        logger.debug("cognito_auth_closed")

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated with valid tokens.

        Returns:
            True if valid non-expired tokens exist.
        """
        try:
            return self._storage.has_valid_tokens()
        except Exception as e:
            logger.warning(
                "auth_check_failed",
                error=str(e),
            )
            return False

    def get_current_tokens(self) -> TokenInfo | None:
        """
        Get current tokens, attempting refresh if expired.

        Returns:
            TokenInfo if available and valid, None otherwise.

        Note:
            This method automatically attempts to refresh expired tokens
            using the stored refresh token.
        """
        try:
            tokens = self._storage.get_tokens()
        except Exception as e:
            logger.warning(
                "token_retrieval_failed",
                error=str(e),
            )
            return None

        if tokens is None:
            return None

        # Check if tokens need refresh (with buffer)
        if tokens.needs_refresh(buffer_seconds=TOKEN_EXPIRY_BUFFER_SECONDS):
            logger.debug("tokens_need_refresh")
            try:
                # Run refresh synchronously
                loop = asyncio.new_event_loop()
                try:
                    refreshed = loop.run_until_complete(
                        self._refresh_tokens(tokens.refresh_token)
                    )
                    if refreshed:
                        return refreshed
                finally:
                    loop.close()
            except Exception as e:
                logger.warning(
                    "token_refresh_failed",
                    error=str(e),
                )
                # Return original tokens if refresh fails but not yet expired
                if not tokens.is_expired():
                    return tokens
                return None

        return tokens

    async def device_flow_login(self) -> AuthResult:
        """
        Perform device/browser OAuth flow.

        Opens a browser for user authentication and waits for
        the callback with the authorization code.

        Returns:
            AuthResult with success/failure status.

        Note:
            This method blocks until the user completes authentication
            in the browser or the timeout is reached.
        """
        correlation_id = get_correlation_id()
        logger.info(
            "device_flow_started",
            correlation_id=correlation_id,
        )

        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self._authorize_url}?{urlencode(auth_params)}"

        # Callback state
        auth_code: str | None = None
        received_state: str | None = None
        error: str | None = None
        redirect_uri = self._redirect_uri

        class CallbackHandler(BaseHTTPRequestHandler):
            """HTTP handler for OAuth callback."""

            def do_GET(self) -> None:
                nonlocal auth_code, received_state, error

                parsed = urlparse(self.path)
                if parsed.path == CALLBACK_PATH:
                    params = parse_qs(parsed.query)

                    if "error" in params:
                        error = params.get("error_description", params["error"])[0]
                        self._send_response(
                            "Authentication failed",
                            "Please close this window and try again.",
                            success=False,
                        )
                    elif "code" in params:
                        auth_code = params["code"][0]
                        received_state = params.get("state", [None])[0]
                        self._send_response(
                            "Authentication Successful",
                            "You can close this window and return to the CLI.",
                            success=True,
                        )
                    else:
                        self._send_response(
                            "Invalid Callback",
                            "Missing authorization code. Please try again.",
                            success=False,
                        )
                else:
                    self.send_error(404)

            def _send_response(
                self,
                title: str,
                message: str,
                success: bool,
            ) -> None:
                """Send HTML response to browser."""
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()

                status_color = "#10b981" if success else "#ef4444"
                status_icon = "&#10003;" if success else "&#10007;"

                html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - AiCippy</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
        }}
        .container {{
            text-align: center;
            padding: 3rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 1rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 400px;
            margin: 1rem;
        }}
        .logo {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .status {{
            width: 4rem;
            height: 4rem;
            border-radius: 50%;
            background: {status_color};
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            font-size: 2rem;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 0.75rem;
        }}
        p {{
            opacity: 0.8;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">AiCippy</div>
        <div class="status">{status_icon}</div>
        <h1>{title}</h1>
        <p>{message}</p>
    </div>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))

            def log_message(self, format: str, *args: Any) -> None:
                """Suppress HTTP server logs."""
                pass

        # Start callback server
        try:
            server = HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)
        except OSError as e:
            logger.error(
                "callback_server_failed",
                error=str(e),
                port=CALLBACK_PORT,
                correlation_id=correlation_id,
            )
            return AuthResult.failure(
                f"Failed to start callback server on port {CALLBACK_PORT}: {e}"
            )

        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        # Open browser
        logger.info(
            "opening_browser",
            url=auth_url[:100] + "...",
            correlation_id=correlation_id,
        )
        webbrowser.open(auth_url)

        # Wait for callback
        server_thread.join(timeout=AUTH_TIMEOUT_SECONDS)
        server.server_close()

        if error:
            logger.warning(
                "auth_error",
                error=error,
                correlation_id=correlation_id,
            )
            return AuthResult.failure(error)

        if not auth_code:
            logger.warning(
                "auth_timeout",
                correlation_id=correlation_id,
            )
            return AuthResult.failure(
                "Authentication timed out or was cancelled"
            )

        if received_state != state:
            logger.error(
                "auth_state_mismatch",
                correlation_id=correlation_id,
            )
            return AuthResult.failure(
                "Invalid state parameter - possible CSRF attack"
            )

        # Exchange code for tokens
        try:
            tokens = await self._exchange_code(auth_code, code_verifier)
            if not tokens:
                return AuthResult.failure("Failed to exchange authorization code")

            # Get user info
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return AuthResult.failure("Failed to get user information")

            # Store credentials securely
            try:
                self._storage.store_tokens(tokens)
                self._storage.store_user_info(user_info.sub, user_info.email)
            except Exception as e:
                logger.error(
                    "credential_storage_failed",
                    error=str(e),
                    correlation_id=correlation_id,
                )
                return AuthResult.failure(f"Failed to store credentials: {e}")

            logger.info(
                "auth_success",
                user_email=user_info.email,
                correlation_id=correlation_id,
            )

            return AuthResult.success_result(
                user_email=user_info.email,
                user_id=user_info.sub,
                expires_at=tokens.expires_at,
                tokens=tokens,
            )

        except Exception as e:
            logger.exception(
                "auth_exchange_failed",
                error=str(e),
                correlation_id=correlation_id,
            )
            return AuthResult.failure(f"Token exchange failed: {e}")

    async def manual_code_login(self) -> AuthResult:
        """
        Perform manual code-based OAuth login.

        Displays the authorization URL for user to copy to browser,
        then prompts for the authorization code to be pasted back.

        Returns:
            AuthResult with success/failure status.
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt
        from rich.text import Text

        console = Console()
        correlation_id = get_correlation_id()
        logger.info(
            "manual_code_login_started",
            correlation_id=correlation_id,
        )

        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self._authorize_url}?{urlencode(auth_params)}"

        # Display compact login panel
        console.print()
        login_content = Text()
        login_content.append("1. ", style="bold cyan")
        login_content.append("Open this URL in your browser:\n\n", style="white")
        login_content.append(f"   {auth_url}\n\n", style="yellow")
        login_content.append("2. ", style="bold cyan")
        login_content.append("Login and copy the ", style="white")
        login_content.append("code", style="bold green")
        login_content.append(" from the redirect URL\n\n", style="white")
        login_content.append("   ", style="dim")
        login_content.append("Format: http://localhost:8765/callback?", style="dim")
        login_content.append("code=XXXXX", style="bold dim")
        login_content.append("&state=...", style="dim")

        console.print(Panel(
            login_content,
            title="[bold #667eea]Login[/bold #667eea]",
            border_style="#667eea",
            padding=(1, 2),
        ))
        console.print()

        # Prompt for authorization code
        auth_code = Prompt.ask("[#667eea]Enter code[/#667eea]")

        if not auth_code or not auth_code.strip():
            logger.warning(
                "manual_code_empty",
                correlation_id=correlation_id,
            )
            console.print("[red]Cancelled.[/red]")
            return AuthResult.failure("No code provided")

        auth_code = auth_code.strip()

        # Prompt for state (for validation)
        received_state = Prompt.ask("[#667eea]Enter state[/#667eea]")

        if not received_state or not received_state.strip():
            logger.warning(
                "manual_state_empty",
                correlation_id=correlation_id,
            )
            console.print("[red]Cancelled.[/red]")
            return AuthResult.failure("No state provided")

        received_state = received_state.strip()

        # Validate state
        if received_state != state:
            logger.error(
                "manual_state_mismatch",
                expected=state[:10] + "...",
                received=received_state[:10] + "...",
                correlation_id=correlation_id,
            )
            console.print("[red]Invalid state. Login cancelled.[/red]")
            return AuthResult.failure("Invalid state")

        # Exchange code for tokens (silent)
        try:
            tokens = await self._exchange_code(auth_code, code_verifier)
            if not tokens:
                console.print("[red]Invalid code. Login cancelled.[/red]")
                return AuthResult.failure("Invalid code")

            # Get user info
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                console.print("[red]Failed to get user info.[/red]")
                return AuthResult.failure("Failed to get user information")

            # Store credentials securely
            try:
                self._storage.store_tokens(tokens)
                self._storage.store_user_info(user_info.sub, user_info.email)
            except Exception as e:
                logger.error(
                    "credential_storage_failed",
                    error=str(e),
                    correlation_id=correlation_id,
                )
                return AuthResult.failure(f"Storage error: {e}")

            logger.info(
                "manual_code_auth_success",
                user_email=user_info.email,
                correlation_id=correlation_id,
            )

            return AuthResult.success_result(
                user_email=user_info.email,
                user_id=user_info.sub,
                expires_at=tokens.expires_at,
                tokens=tokens,
            )

        except Exception as e:
            logger.exception(
                "manual_code_exchange_failed",
                error=str(e),
                correlation_id=correlation_id,
            )
            console.print("[red]Login failed.[/red]")
            return AuthResult.failure(f"Login failed")

    @async_retry(max_attempts=3, min_wait=0.5, max_wait=5.0)
    async def _exchange_code(
        self,
        code: str,
        code_verifier: str,
    ) -> TokenInfo | None:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.
            code_verifier: PKCE code verifier.

        Returns:
            TokenInfo if successful, None otherwise.
        """
        correlation_id = get_correlation_id()
        client = await self._get_client()

        data = {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": self._redirect_uri,
        }

        try:
            response = await client.post(
                self._token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as e:
            logger.error(
                "token_exchange_http_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            return None

        if response.status_code != 200:
            logger.error(
                "token_exchange_failed",
                status=response.status_code,
                response=response.text[:500],
                correlation_id=correlation_id,
            )
            return None

        try:
            token_data = response.json()
        except ValueError as e:
            logger.error(
                "token_exchange_json_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            return None

        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )

        return TokenInfo(
            access_token=token_data["access_token"],
            id_token=token_data["id_token"],
            refresh_token=token_data["refresh_token"],
            expires_at=expires_at,
            token_type=token_data.get("token_type", "Bearer"),
        )

    @async_retry(max_attempts=3, min_wait=0.5, max_wait=5.0)
    async def _refresh_tokens(self, refresh_token: str) -> TokenInfo | None:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token.

        Returns:
            New TokenInfo if successful, None otherwise.

        Raises:
            TokenRefreshError: If refresh fails after retries.
        """
        correlation_id = get_correlation_id()
        client = await self._get_client()

        data = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "refresh_token": refresh_token,
        }

        try:
            response = await client.post(
                self._token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as e:
            logger.warning(
                "token_refresh_http_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            raise TokenRefreshError(
                f"HTTP error during token refresh: {e}",
                context=ErrorContext(
                    correlation_id=correlation_id,
                    operation="token_refresh",
                ),
            ) from e

        if response.status_code != 200:
            logger.warning(
                "token_refresh_failed",
                status=response.status_code,
                correlation_id=correlation_id,
            )
            # Don't raise for 400 errors (invalid token) - just return None
            if response.status_code == 400:
                return None
            raise TokenRefreshError(
                f"Token refresh failed with status {response.status_code}",
                context=ErrorContext(
                    correlation_id=correlation_id,
                    operation="token_refresh",
                ),
            )

        try:
            token_data = response.json()
        except ValueError as e:
            logger.warning(
                "token_refresh_json_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            return None

        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )

        tokens = TokenInfo(
            access_token=token_data["access_token"],
            id_token=token_data["id_token"],
            refresh_token=token_data.get("refresh_token", refresh_token),
            expires_at=expires_at,
            token_type=token_data.get("token_type", "Bearer"),
        )

        # Store refreshed tokens
        try:
            self._storage.store_tokens(tokens)
        except Exception as e:
            logger.warning(
                "token_storage_after_refresh_failed",
                error=str(e),
                correlation_id=correlation_id,
            )

        logger.info(
            "tokens_refreshed",
            expires_at=expires_at.isoformat(),
            correlation_id=correlation_id,
        )

        return tokens

    @async_retry(max_attempts=2, min_wait=0.5, max_wait=2.0)
    async def _get_user_info(self, access_token: str) -> UserInfo | None:
        """
        Get user information from Cognito.

        Args:
            access_token: Valid access token.

        Returns:
            UserInfo if successful, None otherwise.
        """
        correlation_id = get_correlation_id()
        client = await self._get_client()

        try:
            response = await client.get(
                self._userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as e:
            logger.error(
                "userinfo_http_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            return None

        if response.status_code != 200:
            logger.error(
                "userinfo_failed",
                status=response.status_code,
                correlation_id=correlation_id,
            )
            return None

        try:
            data = response.json()
        except ValueError as e:
            logger.error(
                "userinfo_json_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            return None

        return UserInfo(
            sub=data["sub"],
            email=data.get("email", ""),
            email_verified=data.get("email_verified", False),
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            phone_number_verified=data.get("phone_number_verified", False),
        )

    def logout(self) -> None:
        """
        Log out and clear all stored credentials.

        This clears:
        - Access, ID, and refresh tokens
        - User information
        - JWKS cache
        """
        correlation_id = get_correlation_id()
        try:
            self._storage.clear_all()
            self._jwks_cache = None
            logger.info(
                "logged_out",
                correlation_id=correlation_id,
            )
        except Exception as e:
            logger.warning(
                "logout_storage_error",
                error=str(e),
                correlation_id=correlation_id,
            )

    async def validate_token(self, token: str) -> bool:
        """
        Validate a JWT token against Cognito's JWKS.

        Args:
            token: JWT token to validate.

        Returns:
            True if token is valid, False otherwise.
        """
        correlation_id = get_correlation_id()

        try:
            # Fetch JWKS if not cached
            if self._jwks_cache is None:
                client = await self._get_client()
                try:
                    response = await client.get(self._jwks_url)
                    if response.status_code != 200:
                        logger.error(
                            "jwks_fetch_failed",
                            status=response.status_code,
                            correlation_id=correlation_id,
                        )
                        return False
                    self._jwks_cache = response.json()
                except httpx.HTTPError as e:
                    logger.error(
                        "jwks_fetch_http_error",
                        error=str(e),
                        correlation_id=correlation_id,
                    )
                    return False

            # Decode header to get key ID
            unverified = jwt.get_unverified_header(token)
            kid = unverified.get("kid")

            if not kid:
                logger.warning(
                    "token_missing_kid",
                    correlation_id=correlation_id,
                )
                return False

            # Find matching key
            key = None
            for k in self._jwks_cache.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break

            if not key:
                logger.warning(
                    "jwks_key_not_found",
                    kid=kid,
                    correlation_id=correlation_id,
                )
                # Clear cache and retry might find the key
                self._jwks_cache = None
                return False

            # Verify the token
            jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=f"https://cognito-idp.{self._region}.amazonaws.com/{self._user_pool_id}",
            )

            return True

        except JWTError as e:
            logger.warning(
                "token_validation_failed",
                error=str(e),
                correlation_id=correlation_id,
            )
            return False
        except Exception as e:
            logger.exception(
                "token_validation_error",
                error=str(e),
                correlation_id=correlation_id,
            )
            return False

    async def __aenter__(self) -> "CognitoAuth":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit with cleanup."""
        await self.close()
