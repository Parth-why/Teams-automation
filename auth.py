"""Authentication module for Smart Teams Assignment Tracker.

Handles Microsoft OAuth2 authentication using MSAL (Microsoft Authentication Library).
Uses legitimate user-registered Microsoft Entra (Azure AD) App Registrations.
Supports interactive browser login, device-code flow, token caching, and error diagnostics.
Never stores passwords or hardcodes client secrets.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import msal

import config

logger = logging.getLogger("SmartAssignmentTracker.auth")


class AuthResult:
    """Encapsulates the result of an authentication attempt."""

    def __init__(
        self,
        success: bool,
        access_token: Optional[str] = None,
        account: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        error_description: Optional[str] = None,
        requires_admin_consent: bool = False,
    ) -> None:
        self.success = success
        self.access_token = access_token
        self.account = account
        self.error = error
        self.error_description = error_description
        self.requires_admin_consent = requires_admin_consent

    def __repr__(self) -> str:
        return f"<AuthResult success={self.success} error={self.error}>"


class MicrosoftAuthenticator:
    """Manages Microsoft identity authentication and token lifecycles."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        authority: Optional[str] = None,
        token_cache_path: Optional[Path] = None,
    ) -> None:
        self.client_id = (client_id or config.AZURE_CLIENT_ID).strip()
        self.authority = (authority or config.AZURE_AUTHORITY).strip()
        self.cache_file = config.TOKEN_CACHE_FILE if token_cache_path is None else token_cache_path
        self.token_cache = msal.SerializableTokenCache()

        self._load_cache()

        self.app: Optional[msal.PublicClientApplication] = None
        if self.client_id:
            self.app = msal.PublicClientApplication(
                client_id=self.client_id,
                authority=self.authority,
                token_cache=self.token_cache,
            )

    def is_configured(self) -> bool:
        """Check if an Azure Client ID has been configured."""
        return bool(self.client_id)

    def _load_cache(self) -> None:
        """Load cached tokens from disk if available."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.token_cache.deserialize(f.read())
                logger.debug("Loaded token cache from %s", self.cache_file)
            except Exception as e:
                logger.warning("Could not load token cache: %s. Starting with empty cache.", e)

    def _save_cache(self) -> None:
        """Save updated tokens to disk if the cache has changed."""
        if self.token_cache.has_state_changed:
            try:
                config.ensure_directories()
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    f.write(self.token_cache.serialize())
                logger.debug("Saved updated token cache to %s", self.cache_file)
            except Exception as e:
                logger.warning("Could not persist token cache: %s", e)

    def get_accounts(self) -> list[dict[str, Any]]:
        """Return list of accounts currently in the cache."""
        if not self.app:
            return []
        return self.app.get_accounts()

    def acquire_token_silent(self, scopes: Optional[list[str]] = None) -> Optional[AuthResult]:
        """Attempt to acquire a token silently from the cache."""
        if not self.app:
            return None

        scopes = scopes or config.GRAPH_SCOPES
        accounts = self.get_accounts()
        if not accounts:
            logger.debug("No cached accounts found for silent token acquisition.")
            return None

        result = self.app.acquire_token_silent(scopes=scopes, account=accounts[0])
        if result and "access_token" in result:
            self._save_cache()
            logger.info("Successfully acquired token silently for user: %s", accounts[0].get("username"))
            return AuthResult(
                success=True,
                access_token=result["access_token"],
                account=accounts[0],
            )

        logger.debug("Silent token acquisition failed or cache expired.")
        return None

    def acquire_token_interactive(
        self,
        scopes: Optional[list[str]] = None,
        prompt: str = "select_account",
    ) -> AuthResult:
        """Acquire token via the system's default browser."""
        if not self.is_configured():
            return self._missing_client_id_error()

        scopes = scopes or config.GRAPH_SCOPES

        # Try silent first
        silent_result = self.acquire_token_silent(scopes)
        if silent_result and silent_result.success:
            return silent_result

        logger.info("Initiating interactive browser login for client %s with scopes: %s", self.client_id, scopes)
        try:
            assert self.app is not None
            result = self.app.acquire_token_interactive(
                scopes=scopes,
                prompt=prompt,
            )
            return self._process_token_response(result)
        except Exception as e:
            logger.error("Interactive authentication exception: %s", e)
            return AuthResult(
                success=False,
                error="InteractiveAuthFailed",
                error_description=str(e),
            )

    def acquire_token_device_flow(
        self,
        scopes: Optional[list[str]] = None,
    ) -> AuthResult:
        """Acquire token via device-code flow (ideal for terminal or remote testing)."""
        if not self.is_configured():
            return self._missing_client_id_error()

        scopes = scopes or config.GRAPH_SCOPES

        # Try silent first
        silent_result = self.acquire_token_silent(scopes)
        if silent_result and silent_result.success:
            return silent_result

        logger.info("Initiating device code authentication flow for client %s with scopes: %s", self.client_id, scopes)
        assert self.app is not None
        flow = self.app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            error_desc = flow.get("error_description", "Failed to initiate device flow")
            logger.error("Device flow initiation failed: %s", error_desc)
            return AuthResult(
                success=False,
                error=flow.get("error", "DeviceFlowFailed"),
                error_description=error_desc,
            )

        # Print user instructions to terminal
        print("\n" + "=" * 60)
        print(" MICROSOFT LOGIN REQUIRED")
        print("=" * 60)
        print(f" 1. Open your browser and go to: {flow['verification_uri']}")
        print(f" 2. Enter code: {flow['user_code']}")
        print(f" 3. Sign in with your VIT Microsoft account")
        print("=" * 60 + "\n")

        try:
            result = self.app.acquire_token_by_device_flow(flow)
            return self._process_token_response(result)
        except Exception as e:
            logger.error("Device flow acquisition exception: %s", e)
            return AuthResult(
                success=False,
                error="DeviceFlowException",
                error_description=str(e),
            )

    def _missing_client_id_error(self) -> AuthResult:
        """Return clear error when no App Registration Client ID is configured."""
        desc = (
            "AZURE_CLIENT_ID is not configured. A registered Microsoft Entra (Azure AD) "
            "Application ID is required for Graph authentication. Please configure AZURE_CLIENT_ID "
            "in your .env file or pass --client-id <YOUR_CLIENT_ID>."
        )
        logger.error(desc)
        return AuthResult(
            success=False,
            error="MissingClientID",
            error_description=desc,
        )

    def _process_token_response(self, result: dict[str, Any]) -> AuthResult:
        """Parse and validate MSAL token response dictionary."""
        if "access_token" in result:
            self._save_cache()
            account = self.get_accounts()[0] if self.get_accounts() else None
            username = account.get("username") if account else "authenticated_user"
            logger.info("Authentication successful for %s", username)
            return AuthResult(
                success=True,
                access_token=result["access_token"],
                account=account,
            )

        error = result.get("error", "UnknownAuthError")
        error_desc = result.get("error_description", "No detailed description provided.")
        logger.error("Authentication failed: [%s] %s", error, error_desc)

        # Check for admin consent requirements
        requires_admin_consent = (
            "AADSTS65001" in error_desc  # Not consented / Requires admin consent
            or "AADSTS90094" in error_desc  # Admin consent required
            or "AADSTS65002" in error_desc  # Preauthorization / consent configuration issue
            or "consent_required" in error
            or "interaction_required" in error_desc
        )

        return AuthResult(
            success=False,
            error=error,
            error_description=error_desc,
            requires_admin_consent=requires_admin_consent,
        )

    def clear_cache(self) -> None:
        """Clear all cached tokens."""
        if self.app:
            for account in self.get_accounts():
                self.app.remove_account(account)
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                logger.info("Cleared token cache file %s", self.cache_file)
            except Exception as e:
                logger.warning("Could not delete cache file: %s", e)
