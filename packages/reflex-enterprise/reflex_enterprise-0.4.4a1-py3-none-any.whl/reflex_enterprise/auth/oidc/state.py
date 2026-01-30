"""Reflex state for OIDC authentication."""

import base64
import contextlib
import dataclasses
import datetime
import hashlib
import logging
import secrets
import sys
import time
import uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Literal
from urllib.parse import parse_qsl, urlencode, urlparse

import httpx
import reflex as rx
from httpx._client import USE_CLIENT_DEFAULT
from joserfc.jwt import Token
from packaging import version
from reflex.utils import console
from reflex.vars import BaseStateMeta

from reflex_enterprise.app import AppEnterprise
from reflex_enterprise.auth.cookie import HTTPCookie
from reflex_enterprise.auth.oidc.config import ConfigMixin
from reflex_enterprise.auth.oidc.types import OIDCUserInfo
from reflex_enterprise.auth.oidc.utils import compute_at_hash, verify_jwt
from reflex_enterprise.components.message_listener import (
    POST_MESSAGE_AND_CLOSE_POPUP,
    WINDOW_OPEN,
    WindowMessage,
    message_listener,
)
from reflex_enterprise.utils import (
    call_event_from_computed_var,
    chain_event_out_of_band,
)

logger = logging.getLogger("reflex_enterprise.auth.oidc")
# Time in seconds to cache access token in computed var (adjusted dynamically
# based on token expiry)
ACCESS_TOKEN_CACHE_INTERVAL = 60  # 1 minute

COOKIE_MAX_AGE = 604800
COOKIE_ACCESS_TOKEN = HTTPCookie(
    max_age=COOKIE_MAX_AGE,
    secure=True,
    same_site="strict",
    _sync_on_set=False,
)
COOKIE_ID_TOKEN = HTTPCookie(
    max_age=COOKIE_MAX_AGE,
    secure=True,
    same_site="strict",
    _sync_on_set=False,
)
COOKIE_REFRESH_TOKEN = HTTPCookie(
    max_age=COOKIE_MAX_AGE,
    secure=True,
    same_site="strict",
    _sync_on_set=False,
)
COOKIE_GRANTED_SCOPES = HTTPCookie(
    max_age=COOKIE_MAX_AGE,
    secure=True,
    same_site="strict",
    _sync_on_set=False,
)


class NestedExceptionError(Exception):
    """Exception raised when an error occurs in a nested error context."""


class DefaultUserErrorMessage(str):
    """Sentinel value for default user error message."""


@dataclasses.dataclass
class AccessTokenMetadata:
    """Metadata about an access token stored in a cookie."""

    access_token: str
    expires_at: float

    @classmethod
    def from_exchange(
        cls, exchange_response: Mapping[str, Any]
    ) -> "AccessTokenMetadata":
        """Create AccessTokenMetadata from token exchange response.

        Args:
            exchange_response: The token exchange response from the OIDC provider.

        Returns:
            An AccessTokenMetadata instance.
        """
        access_token = exchange_response["access_token"]
        expires_in = exchange_response.get("expires_in")
        if expires_in is not None:
            expires_at = time.time() + int(expires_in)
        else:
            expires_at = float("inf")
        return cls(
            access_token=access_token,
            expires_at=expires_at,
        )

    @classmethod
    def from_cookie_value(cls, at_data_qs: str) -> "AccessTokenMetadata | None":
        """Parse the access token metadata from the cookie value.

        Args:
            at_data_qs: The access token data query string from the cookie.

        Returns:
            An AccessTokenMetadata instance or None if parsing fails.
        """
        try:
            data = dict(parse_qsl(at_data_qs))
        except Exception:
            return None
        if not data or not (access_token := data.get("access_token")):
            return None
        try:
            expires_at = float(data["expires_at"])
        except (KeyError, TypeError, ValueError):
            expires_at = float("inf")
        return cls(
            access_token=access_token,
            expires_at=expires_at,
        )

    def to_cookie_value(self) -> str:
        """Serialize the access token metadata to a cookie value.

        Returns:
            The access token metadata as a query string.
        """
        return urlencode(
            {
                "access_token": self.access_token,
                "expires_at": str(self.expires_at),
            }
        )


class OIDCCookieMeta(BaseStateMeta):
    """Meta class to assign HTTPCookie descriptors to the final class."""

    if TYPE_CHECKING:
        _access_token_data: str = COOKIE_ACCESS_TOKEN
        _id_token: str = COOKIE_ID_TOKEN
        _granted_scopes: str = COOKIE_GRANTED_SCOPES
        _refresh_token: str = COOKIE_REFRESH_TOKEN

    def __new__(cls, name: str, bases: tuple, attrs: dict[str, Any], **kwargs):
        """Assign HTTPCookie descriptors to the final class."""
        if not kwargs.get("mixin"):
            inherited_fields = {}
            for base in bases[::-1]:
                if hasattr(base, "__inherited_fields__"):
                    inherited_fields.update(base.__inherited_fields__)

            provider = attrs.get("__provider__", "generic")
            annotations = attrs.setdefault("__annotations__", {})

            def apply_cookie(name: str, cookie: HTTPCookie):
                if name not in inherited_fields:
                    annotations[name] = str
                    attrs[name] = cookie._replace(name=f"_oidc_{provider}{name}")

            apply_cookie("_access_token_data", COOKIE_ACCESS_TOKEN)
            apply_cookie("_id_token", COOKIE_ID_TOKEN)
            apply_cookie("_refresh_token", COOKIE_REFRESH_TOKEN)
            apply_cookie("_granted_scopes", COOKIE_GRANTED_SCOPES)
        return super().__new__(cls, name, bases, attrs, **kwargs)


class OIDCAuthState(ConfigMixin, rx.State, mixin=True, metaclass=OIDCCookieMeta):
    """Reflex base state class for managing OIDC authentication flows.

    This state class handles the OAuth 2.0 Authorization Code flow with PKCE
    for OIDC authentication, including token storage, validation, and user
    information retrieval.

    Users should subclass this state and set the `__provider__` attribute
    to specify the OIDC provider (e.g., "okta", "databricks"), and supply
    appropriate environment variables for client ID, secret, and issuer URI.

    For example:
    ```python
    class OktaAuthState(OIDCAuthState, rx.State):
        __provider__ = "okta"
    ```

    Then use the `OktaAuthState.get_login_button()` method to render a login
    button in your app.

    Attributes:
        access_token: The OAuth 2.0 access token stored in cookie.
        id_token: The OpenID Connect ID token stored in cookie.
        granted_scopes: The scopes granted for the access_token stored in cookie.
        is_iframed: Whether the app is running inside an iframe.
        from_popup: Whether the current page was opened as a popup.

        _redirect_to_url: URL to redirect to after successful authentication.
        _app_state: Random state parameter for CSRF protection.
        _code_verifier: PKCE code verifier for secure authorization.
        _requested_scopes: Scopes requested during authentication.
        _last_error_message: Error message for authentication failures.
    """

    __provider__: ClassVar[str] = "generic"
    _has_registered_endpoints: ClassVar[bool] = False
    _logger: ClassVar[logging.Logger] = logger
    _default_user_error_message: ClassVar[str] = (
        "Authentication error, please try again."
    )

    is_iframed: bool = False
    from_popup: bool = False
    user_error_message: str

    _redirect_to_url: str
    _app_state: str
    _code_verifier: str
    _requested_scopes: str = "openid email profile"
    _nonce: str | None = None
    _expected_at_hash: str | None = None
    _error_context_depth: int = 0
    _last_error_message: str
    _last_error_txid: str
    _last_auth_callback_exchange: dict | None = None
    _last_refreshed_access_token: float = 0.0

    @rx.var(
        interval=COOKIE_MAX_AGE,
        deps=["_access_token_data"],
        auto_deps=False,
        initial_value=None,
    )
    def _access_token_metadata(self) -> AccessTokenMetadata | None:
        """Get the access token metadata from the cookie."""
        return AccessTokenMetadata.from_cookie_value(self._access_token_data)

    @rx.var(
        interval=ACCESS_TOKEN_CACHE_INTERVAL,
        deps=["_access_token_metadata"],
        auto_deps=False,
        initial_value="",
    )
    async def _access_token(self) -> str:
        """Get the access token from the cookie."""
        if (at_metadata := self._access_token_metadata) is None:
            return ""
        # Handle refreshing the token if needed.
        if at_metadata.expires_at < time.time():
            if self._last_refreshed_access_token >= at_metadata.expires_at:
                # We're already refreshing, so just return the token we currently have.
                return at_metadata.access_token
            if self._refresh_token:
                self._last_refreshed_access_token = at_metadata.expires_at
                return await self._refresh_access_token()
            await call_event_from_computed_var(self, type(self).reset_auth)
            return ""
        return at_metadata.access_token

    async def _update_access_token_cache_expiry(self):
        """Update the access token computed var cache expiry based on token metadata."""
        if (at_metadata := self._access_token_metadata) is not None:
            new_update_time = datetime.datetime.fromtimestamp(
                at_metadata.expires_at
            ) - datetime.timedelta(seconds=ACCESS_TOKEN_CACHE_INTERVAL * 2)
            setattr(
                self,
                self.computed_vars["_access_token"]._last_updated_attr,
                new_update_time,
            )

    @rx.var(deps=["_access_token", "_id_token"], auto_deps=False, initial_value=False)
    async def has_any_token(self) -> bool:
        """Whether any authentication token is present."""
        has_any_token = bool((await self._access_token) or self._id_token)
        # This var updates whenever _access_token changes, so fix the _access_token cache expiry time here.
        await self._update_access_token_cache_expiry()
        return has_any_token

    @rx.var(initial_value="")
    def granted_scopes(self) -> str:
        """Get the granted scopes from the cookie."""
        return self._granted_scopes or ""

    @rx.event
    def reset_auth(self):
        """Reset authentication state and clear tokens."""
        del self._access_token_data
        del self._id_token
        del self._refresh_token
        del self._granted_scopes
        self._logger.debug(self._format_log_message("Reset auth cookies"))
        return HTTPCookie.sync()

    async def _verify_jwt(self, token_json: str) -> Token:
        """Subclasses can override to customize id_token JWT verification.

        Args:
            token_json: The JWT as a string.

        Returns:
            The verified Token object.
        """
        return await verify_jwt(
            token_json,
            issuer=await self._issuer_uri(),
            audience=await self._client_id(),
            nonce=self._nonce,
            at_hash=self._expected_at_hash,
        )

    async def _validate_tokens(self) -> bool:
        """Subclasses can override to customize access_token and id_token validation.

        Returns:
            True if tokens are valid, False otherwise.
        """
        if not await self._access_token or not self._id_token:
            return False

        async with self._error_context(
            "ID Token verification",
            user_error_message=None,
        ) as errors:
            await self._verify_jwt(self._id_token)
        return not errors

    def _ensure_last_error_txid(self):
        """Ensure there is a transaction ID for logging correlation."""
        if not self._last_error_txid:
            self._last_error_txid = uuid.uuid4().hex

    def _clear_last_error(self):
        """Called when starting a new auth operation to clear previous saved errors."""
        self.user_error_message = ""
        self._error_context_depth = 0
        self._last_error_message = ""
        self._last_error_txid = ""
        self._ensure_last_error_txid()

    def _format_log_message(self, msg: str) -> str:
        """Format a log message with client token and transaction ID.

        Args:
            msg: The message to format.

        Returns:
            The formatted log message.
        """
        error_context_prefix = "".join(
            [
                " " if self._error_context_depth > 1 else "",
                "─" * max(self._error_context_depth - 1, 0),
            ]
        )
        self._ensure_last_error_txid()
        return (
            f"{self.router.session.client_token} "
            f"[txid={self._last_error_txid}]{error_context_prefix} {msg}"
        )

    def _set_last_error_message(
        self, msg: str, user_error_message: str | None = DefaultUserErrorMessage()
    ):
        """Store and log the last error message and user-facing error message.

        Args:
            msg: The error message to set and log.
            user_error_message: Message to show to the user via toast.

        Returns:
            A toast component with the user error message, or None.
        """
        self._last_error_message = msg
        self._logger.info(
            self._format_log_message(self._last_error_message), exc_info=sys.exc_info()
        )
        if isinstance(user_error_message, DefaultUserErrorMessage):
            user_error_message = self._default_user_error_message
        if user_error_message is not None:
            self.user_error_message = user_error_message
            return rx.toast.error(user_error_message)
        return None

    @contextlib.asynccontextmanager
    async def _error_context(
        self,
        operation: str,
        user_error_message: str | None = DefaultUserErrorMessage(),
        clear_last_error: bool = False,
    ):
        """Async context manager to wrap auth operations and handle errors.

        Args:
            operation: Description of the operation being performed.
            user_error_message: Message to show to the user via toast on error.
            clear_last_error: Whether to clear the last error at the start.

        Yields: a list of exceptions encountered in the block.
        """
        if clear_last_error:
            self._clear_last_error()
        self._error_context_depth += 1
        self._logger.debug(self._format_log_message(f"{operation}"))
        exceptions = []
        try:
            yield exceptions
        except NestedExceptionError as nested_exc:
            exceptions.append(nested_exc.__cause__ or nested_exc)
            # No re-logging or re-toasting for nested exceptions, just stop processing.
            return
        except Exception as e:
            exceptions.append(e)
            if (
                error_toast := self._set_last_error_message(
                    f"{operation} failed: {e}",
                    user_error_message=user_error_message,
                )
            ) is not None:
                await chain_event_out_of_band(self, error_toast)
            if self._error_context_depth > 1:
                # Also raise the error in nested contexts to stop further processing.
                raise NestedExceptionError from e
        finally:
            self._error_context_depth = max(self._error_context_depth - 1, 0)

    @rx.var(initial_value=False)
    def has_error(self) -> bool:
        """Whether there was an authentication error."""
        return bool(self._last_error_message)

    @rx.var
    def last_error_txid(self) -> str:
        """Get the last error transaction ID for logging correlation."""
        return self._last_error_txid

    @rx.var(
        interval=datetime.timedelta(minutes=30),
        deps=["_access_token", "_id_token"],
        auto_deps=False,
        initial_value=None,
    )
    async def userinfo(self) -> OIDCUserInfo | None:
        """Get the authenticated user's information from OIDC token.

        This property retrieves the user's profile information from the OIDC
        userinfo endpoint using the stored access token. The result is cached
        for 30 minutes and automatically revalidated.

        Returns:
            OIDCUserInfo or subclass containing user profile data if authentication is valid,
            None if tokens are invalid or the request fails.
        """
        if not self._id_token:
            return None

        # Get the latest userinfo
        async with self._error_context("Fetching userinfo", user_error_message=None):
            if not await self._validate_tokens():
                if (
                    self._access_token_metadata is not None
                    and self._last_refreshed_access_token
                    < self._access_token_metadata.expires_at
                ):
                    await call_event_from_computed_var(self, type(self).reset_auth)
                return None
            if (
                userinfo_endpoint := await self._issuer_endpoint("userinfo_endpoint")
            ) and (access_token := await self._access_token):
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        userinfo_endpoint,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    resp.raise_for_status()
                    return resp.json()  # pyright: ignore[reportReturnType]
            # Have to just trust the ID token claims.
            return (await self._verify_jwt(self._id_token)).claims  # pyright: ignore[reportReturnType]

    def _redirect_uri(self) -> str:
        """Construct the redirect URI for the OAuth 2.0 authorization code flow.

        This must match the redirect URI registered with the OIDC provider.

        Returns:
            The redirect URI as a string.
        """
        current_url = urlparse(self.router.url)
        return current_url._replace(
            path=self._authorization_code_endpoint(),
            query=None,
            fragment=None,
        ).geturl()

    def _index_uri(self) -> str:
        """Get the app's index URI.

        Returns:
            The current page's url without path, query, or fragment.
        """
        current_url = urlparse(self.router.url)
        return current_url._replace(path="/", query=None, fragment=None).geturl()

    async def _popup_login_url(self) -> str:
        """Get the popup login endpoint URL.

        Returns:
            The popup login endpoint URL.
        """
        return self._popup_login_endpoint()

    async def _popup_login_options(self) -> tuple[str, str]:
        """Get the popup login window name and features.

        Returns:
            A tuple of (window_name, window_features).
        """
        window_name = f"{self.__provider__}_popup_login"
        window_features = "width=600,height=600"
        return window_name, window_features

    _popup_logout_options = _popup_login_options

    @rx.event
    async def redirect_to_login_popup(self):
        """Open a small popup window to initiate the login flow.

        This is used when the app detects it's embedded and needs to open a
        dedicated popup for the authorization flow.
        """
        window_name, window_features = await self._popup_login_options()
        return rx.call_script(
            WINDOW_OPEN(
                await self._popup_login_url(),
                window_name,
                window_features,
            )
        )

    async def _popup_logout_url(self) -> str:
        """Get the popup logout endpoint URL.

        Returns:
            The popup logout endpoint URL.
        """
        return self._popup_logout_endpoint()

    @rx.event
    async def redirect_to_logout_popup(self):
        """Open a small popup window to initiate the logout flow."""
        window_name, window_features = await self._popup_logout_options()
        return rx.call_script(
            WINDOW_OPEN(
                await self._popup_logout_url(),
                window_name,
                window_features,
            )
        )

    @rx.event
    def set_from_popup(self, from_popup: bool):
        """Set whether the current page was opened as a popup."""
        self.from_popup = from_popup
        if from_popup:
            return type(self).popup_on_load()

    @rx.event
    def popup_on_load(self):
        """Handler to run when a popup login or logout page is loaded."""

    async def _redirect_to_login_payload(self) -> dict:
        """Get the payload for initial authorization request.

        Returns:
            A dictionary containing any necessary parameters for login redirection.
        """
        # store app state and code verifier in session
        self._app_state = secrets.token_urlsafe(64)
        self._code_verifier = secrets.token_urlsafe(64)
        self._redirect_to_url = self.router.url

        # calculate code challenge
        hashed = hashlib.sha256(self._code_verifier.encode("ascii")).digest()
        encoded = base64.urlsafe_b64encode(hashed)
        code_challenge = encoded.decode("ascii").strip("=")

        # get request params
        return {
            "client_id": await self._client_id(),
            "redirect_uri": self._redirect_uri(),
            "scope": self._requested_scopes,
            "state": self._app_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_type": "code",
            "response_mode": "query",
        }

    @rx.event
    async def redirect_to_login(self):
        """Initiate the OAuth 2.0 authorization code flow with PKCE.

        This method generates the necessary state and code verifier for PKCE,
        constructs the authorization URL, and redirects the user to OIDC
        authorization endpoint.

        If the user's token is already valid (popup flow), then post the tokens
        to the opener and display the success toast.

        Returns:
            - If iframed, a script to open the login popup window.
            - If already authenticated, a post-authentication window message event and success toast
            - If login flow cannot be initiated due to error, None.
            - A redirect response to the provider's OIDC authorization endpoint
        """
        if self.is_iframed:
            return type(self).redirect_to_login_popup()

        async with self._error_context("Processing login flow", clear_last_error=True):
            if await self._validate_tokens():
                return [
                    self.__class__.post_auth_message,
                    rx.toast("You are logged in."),
                ]
            async with self._error_context("Building authorization request"):
                query_params = await self._redirect_to_login_payload()
                request_uri = f"{await self._issuer_endpoint('authorization_endpoint')}?{urlencode(query_params)}"
                return rx.redirect(request_uri)

    async def _redirect_to_logout_payload(self) -> dict[str, str]:
        """Get the payload for initiating logout request.

        Returns:
            A dictionary containing any necessary parameters for logout redirection.
        """
        self._app_state = secrets.token_urlsafe(64)
        query_params = {
            "state": self._app_state,
        }
        if self._id_token:
            query_params["id_token_hint"] = self._id_token
        post_logout_redirect_uri = self._index_uri()
        if self.from_popup:
            post_logout_redirect_uri = (
                post_logout_redirect_uri.rstrip("/") + await self._popup_logout_url()
            )
        query_params["post_logout_redirect_uri"] = post_logout_redirect_uri
        return query_params

    @rx.event
    async def redirect_to_logout(self):
        """Initiate the OAuth 2.0 logout flow.

        This method generates a new state parameter, constructs the logout URL
        with the ID token hint, and redirects the user to OIDC's logout endpoint.

        The user's tokens are cleared from cookies after this event.

        Returns:
            - If iframed, a script to open the logout popup window if supported by the provider.
            - If logout flow cannot be initiated due to error or omission, None.
            - A redirect response to the provider's OIDC end_session endpoint
        """
        from_popup = self.from_popup
        async with self._error_context(
            f"Processing logout flow ({from_popup=})",
            user_error_message="Logout error",
            clear_last_error=True,
        ):
            end_session_endpoint = await self._issuer_endpoint("end_session_endpoint")
            if self.is_iframed:
                if end_session_endpoint:
                    # Open the logout popup when the provider gives a logout endpoint.
                    yield type(self).redirect_to_logout_popup()
                else:
                    # Otherwise, reset the tokens and the app is effectively logged out.
                    yield self.reset_auth()
                return
            try:
                # Get the logout redirect payload while we still have the tokens.
                query_params = await self._redirect_to_logout_payload()
            finally:
                # Clear browser tokens after user requested logout.
                yield self.reset_auth()
                # Also clear browser tokens in opener from the popup.
                if from_popup:
                    yield type(self).post_logout_message
            # Redirect to initiate provider logout flow.
            if end_session_endpoint:
                request_uri = f"{end_session_endpoint}?{urlencode(query_params)}"
                yield rx.redirect(request_uri)

    async def _validate_auth_callback_request_params(
        self, request_params: Mapping[str, Any]
    ) -> Literal[True]:
        """Validate the auth callback request parameters.

        Args:
            request_params: The request parameters from the callback.

        Returns:
            True if the request parameters are valid.

        Raises:
            ValueError: If the request parameters are invalid.
        """
        app_state = request_params.get("state")
        if app_state != self._app_state:
            raise ValueError("App state mismatch. Possible CSRF attack.")
        return True

    async def _auth_callback_payload_from_request_params(
        self, request_params: Mapping[str, Any]
    ) -> dict[str, str]:
        """Get the payload for the token exchange request from auth callback request parameters.

        Args:
            request_params: The request parameters from the callback.

        Returns:
            A dictionary containing the necessary parameters for the auth callback.

        Raises:
            ValueError: If any required parameters are missing.
        """
        if not (code := request_params.get("code")):
            raise ValueError("No code provided in the callback.")
        query_params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._redirect_uri(),
            "code_verifier": self._code_verifier,
            "scope": self._requested_scopes,
        }
        if not await self._client_secret():
            query_params["client_id"] = await self._client_id()
        return query_params

    async def _auth_callback_authorization(self) -> tuple[str, str] | None:
        """Get the authorization tuple for the token exchange request.

        Returns:
            A tuple of (client_id, client_secret) if client_secret is set,
            None otherwise.
        """
        if client_secret := await self._client_secret():
            return (await self._client_id(), client_secret)
        return None

    async def _validate_auth_callback_exchange(
        self, exchange: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        """Validate the token exchange response from the auth callback.

        Subclasses may override this method to implement additional validation
        logic on the token exchange response.

        Args:
            exchange: The token exchange dictionary.

        Returns:
            The validated exchange dictionary if valid, None otherwise.

        Raises:
            ValueError: If the exchange is invalid.
        """
        if exchange.get("token_type") != "Bearer":
            raise ValueError("Unsupported token type. Should be 'Bearer'.")
        return dict(exchange)

    async def _set_tokens_payload_from_exchange(
        self, exchange: Mapping[str, Any]
    ) -> dict[str, str]:
        """Get the payload for setting tokens from the token exchange.

        The returned value will be passed as keyword arguments to `_set_tokens`.

        Args:
            exchange: The token exchange dictionary.

        Returns:
            A dictionary containing the authentication tokens and scopes.
        """
        return {
            "access_token": AccessTokenMetadata.from_exchange(
                exchange
            ).to_cookie_value(),
            "id_token": exchange.get("id_token", ""),
            "refresh_token": exchange.get("refresh_token", ""),
            "granted_scopes": exchange.get("scope", ""),
        }

    @rx.event
    async def auth_callback(self):
        """Handle the OAuth 2.0 authorization-code callback.

        This method is called when the user is redirected back from OIDC
        authorization endpoint. It validates the state parameter to prevent CSRF
        attacks, exchanges the authorization code for tokens using PKCE, and
        stores the tokens for future use.

        Returns:
            A redirect response to the original requested URL, or an error toast
            if authentication fails.
        """
        self._last_auth_callback_exchange = None
        async with self._error_context(
            "Processing auth callback", clear_last_error=True
        ):
            async with self._error_context("Validating auth callback request"):
                await self._validate_auth_callback_request_params(
                    self.router.url.query_parameters
                )
            async with self._error_context("Building token request payload"):
                query_params = await self._auth_callback_payload_from_request_params(
                    self.router.url.query_parameters
                )
                auth = (await self._auth_callback_authorization()) or USE_CLIENT_DEFAULT
            async with (
                self._error_context("Exchanging authorization code for tokens"),
                httpx.AsyncClient() as client,
            ):
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                resp = await client.post(
                    await self._issuer_endpoint("token_endpoint"),
                    headers=headers,
                    data=query_params,
                    auth=auth,
                )
                resp.raise_for_status()
                if exchange := (
                    await self._validate_auth_callback_exchange(resp.json())
                ):
                    self._last_auth_callback_exchange = exchange
                else:
                    return
            # Store tokens.
            async with self._error_context("Setting authentication tokens"):
                await self._set_tokens(
                    **await self._set_tokens_payload_from_exchange(
                        self._last_auth_callback_exchange
                    )
                )
                return [
                    HTTPCookie.sync(),
                    rx.redirect(self._redirect_to_url),
                ]

    async def _refresh_access_token_payload(self) -> dict[str, str]:
        """Get the payload for refreshing the access token.

        Returns:
            A dictionary containing the necessary parameters for token refresh.
        """
        query_params = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "scope": self._requested_scopes,
        }
        if not await self._client_secret():
            query_params["client_id"] = await self._client_id()
        return query_params

    async def _refresh_access_token(self) -> str:
        """Refresh the access token using the refresh token.

        Returns:
            The new access token as a string.

        Raises:
            Exception: If the token refresh fails.
        """
        async with self._error_context("Refreshing access token"):
            query_params = await self._refresh_access_token_payload()
            auth = (await self._auth_callback_authorization()) or USE_CLIENT_DEFAULT
            async with httpx.AsyncClient() as client:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                resp = await client.post(
                    await self._issuer_endpoint("token_endpoint"),
                    headers=headers,
                    data=query_params,
                    auth=auth,
                )
                resp.raise_for_status()
                exchange = await self._validate_auth_callback_exchange(resp.json())
                if not exchange:
                    raise ValueError("Invalid token refresh response.")
                await self._set_tokens(
                    **await self._set_tokens_payload_from_exchange(exchange)
                )
                await chain_event_out_of_band(self, HTTPCookie.sync())
                return exchange.get("access_token", "")
        return ""

    async def _set_tokens(
        self,
        access_token: str,
        id_token: str,
        refresh_token: str = "",
        granted_scopes: str = "",
        **kwargs,
    ):
        """Validate and set the authentication tokens in state.

        Subclasses may override this method when handling additional data
        returned from the token exchange that must be persisted in the state or
        validated in some way.

        Args:
            access_token: The urlencoded OAuth 2.0 access token and expires_at value.
            id_token: The OpenID Connect ID token.
            refresh_token: The OAuth 2.0 refresh token.
            granted_scopes: The scopes granted for the access_token.
            kwargs: Additional keyword arguments (ignored in default implementation).
        """
        self._access_token_data = access_token
        self._logger.debug(self._format_log_message("Set access token cookie"))
        self._id_token = id_token
        self._refresh_token = refresh_token
        self._granted_scopes = granted_scopes
        self._nonce = None
        self._expected_at_hash = None

        # compute at_hash and store for additional validation
        try:
            token = await self._verify_jwt(id_token)
            alg = token.header.get("alg")
            at_hash = compute_at_hash(await self._access_token, alg)
            # store expected at_hash in a transient property (not persisted)
            self._expected_at_hash = at_hash
        except Exception:
            self._expected_at_hash = None

        # Validate again after setting expected_at_hash
        if not await self._validate_tokens():
            self.reset_auth()

    @rx.var
    def origin(self) -> str:
        """Return the app origin URL (used as postMessage target origin)."""
        return self._index_uri().rstrip("/")

    @rx.event
    def check_if_iframed(self):
        """Run a short client-side check to determine whether the page is iframed.

        The result is reported to `check_if_iframed_cb`.
        """
        if not self._access_token_data:
            # When the websocket hasn't sent the cookies, schedule a manual sync
            # when the auth route loads.
            yield HTTPCookie.sync()
        return rx.call_function(
            """() => {
    try {
        return window.self !== window.top;
    } catch (e) {
        // This catch block handles potential security errors (Same-Origin Policy)
        // if the iframe content and the parent are from different origins.
        // In such cases, access to window.top might be restricted, implying it's in an iframe.
        return true;
    }
}""",
            callback=type(self).check_if_iframed_cb,
        )

    @rx.event
    def check_if_iframed_cb(self, is_iframed: bool):
        """Callback invoked with the iframe detection result.

        Args:
            is_iframed: True if the page is inside an iframe or cross-origin
                access prevented detection.
        """
        self.is_iframed = is_iframed

    @rx.event
    async def on_iframe_auth_success(self, event: WindowMessage):
        """Handle an authentication success or logout message posted from a child window.

        The auth message payload is expected to include `access_token`, `id_token`,
        and an optional `nonce`. Tokens are stored via `_set_tokens`.
        """
        if event["data"].get("type") == f"post_logout_{self.__provider__}":
            yield self.reset_auth()
        if event["data"].get("type") != f"post_auth_{self.__provider__}":
            return
        event_data = event["data"].copy()
        event_data.pop("type", None)
        async with self._error_context(
            "Processing iframe auth success", clear_last_error=True
        ):
            await self._set_tokens(
                access_token=event_data.pop("access_token"),
                id_token=event_data.pop("id_token"),
                refresh_token=event_data.pop("refresh_token", ""),
                granted_scopes=event_data.pop("scope", ""),
                **event_data,
            )
            yield HTTPCookie.sync()

    async def _post_auth_message_payload(self) -> dict[str, str]:
        """Get the payload for the post-authentication window message.

        The returned value will be received by on_iframe_auth_success and
        ultimately passed to `_set_tokens`.

        Returns:
            A dictionary containing the authentication tokens and scopes.
        """
        return {
            "access_token": self._access_token_data,
            "id_token": self._id_token,
            "refresh_token": self._refresh_token,
            "scope": self._granted_scopes,
        }

    @rx.event
    async def post_auth_message(self):
        """Post tokens back to the opening window and close the popup.

        This is called on the popup page when authentication has completed and
        the tokens are available in `self._access_token` / `self._id_token`.
        """
        async with self._error_context("Posting auth message to opener"):
            payload = {
                "type": f"post_auth_{self.__provider__}",
                **(await self._post_auth_message_payload()),
            }
            return rx.call_script(
                POST_MESSAGE_AND_CLOSE_POPUP(payload, self.origin, 500)
            )

    @rx.event
    async def post_logout_message(self):
        """Post logout message back to the opening window and close the popup.

        This is called on the popup page when logout has completed.
        """
        async with self._error_context("Posting logout message to opener"):
            payload = {
                "type": f"post_logout_{self.__provider__}",
            }
            return rx.call_script(
                POST_MESSAGE_AND_CLOSE_POPUP(payload, self.origin, 500)
            )

    @classmethod
    def get_login_button(cls, *children) -> rx.Component:
        """Return a login button component that initiates OIDC auth.

        If `children` are provided they will be placed inside the clickable
        element; otherwise a default button label is used. The component wires up
        the message listener (for iframe flows), the click handler, and a mount
        handler that checks whether the page is embedded in an iframe.
        """
        cls.register_auth_endpoints()
        if not children:
            children = [rx.button(f"Login with {cls.__provider__.title()}")]
        return rx.el.div(
            *children,
            rx.cond(
                cls.is_iframed,
                message_listener(
                    allowed_origin=cls.origin,
                    on_message=cls.on_iframe_auth_success,
                ),
            ),
            on_click=cls.redirect_to_login,
            on_mount=cls.check_if_iframed,
            width="fit-content",
        )

    @classmethod
    def get_state_hydrating_component(cls) -> rx.Component:
        """Loading spinner shown before state is hydrated."""
        return rx.vstack(
            rx.spinner(),
            align="center",
            justify="center",
            height="50vh",
            width="100%",
        )

    @classmethod
    def _with_hydrated(cls, *components: rx.Component) -> rx.Component:
        """Wrap components to wait for state hydration before rendering.

        Args:
            components: The components to render after hydration.

        Returns:
            A component that shows a loading spinner until state is hydrated,
            then renders the provided components.
        """
        return rx.cond(
            rx.State.is_hydrated,
            rx.fragment(*components),
            cls.get_state_hydrating_component(),
        )

    @classmethod
    def get_authentication_loading_page(cls) -> rx.Component:
        """Small loading page shown while authentication is validated.

        This page is registered by the package as the callback target when the
        authorization response is being processed.
        """
        return rx.container(
            cls._with_hydrated(
                rx.cond(
                    cls.has_error,
                    rx.vstack(
                        rx.heading("An error occurred during authentication."),
                        rx.text(
                            "Please close this window and try again.",
                        ),
                        rx.text(
                            "An administrator may provide more information about error ID: ",
                            rx.badge(cls.last_error_txid),
                        ),
                    ),
                    rx.cond(
                        ~cls.userinfo,
                        rx.hstack(
                            rx.heading("Validating Authentication..."),
                            rx.spinner(),
                            width="50%",
                            justify="between",
                        ),
                        rx.heading("Redirecting to app..."),
                    ),
                ),
            ),
        )

    @classmethod
    def get_authentication_popup_logout(cls) -> rx.Component:
        """Simple page shown during the logout flow.

        Registered at `/_reflex_oidc_{provider}/popup-logout` to complete the sign-out handshake.
        """
        return rx.container(
            cls._with_hydrated(
                rx.cond(
                    cls.has_error,
                    rx.vstack(
                        rx.heading("An error occurred during logout."),
                        rx.text(
                            "You close this window and clear browser cookies to manually log out.",
                        ),
                        rx.text(
                            "An administrator may provide more information about error ID: ",
                            rx.badge(cls.last_error_txid),
                        ),
                    ),
                    rx.cond(
                        cls.has_any_token,
                        rx.hstack(
                            rx.heading("Complete logout process."),
                            rx.spinner(),
                            width="50%",
                            justify="between",
                        ),
                        rx.heading("You are logged out. You may close this window."),
                    ),
                ),
            ),
        )

    @classmethod
    def register_auth_endpoints(cls, app: AppEnterprise | None = None):
        """Register the Okta authentication endpoints with the Reflex app.

        This function sets up the necessary OAuth callback endpoint for handling
        authentication responses from OIDC providers. The callback endpoint
        handles the authorization code exchange and redirects users.
        """
        if app is None and cls._has_registered_endpoints:
            return
        if app is None:
            cls._has_registered_endpoints = True

            from reflex.utils.prerequisites import get_app

            app = get_app().app
        if not isinstance(app, AppEnterprise):
            raise TypeError("The app must be an instance of reflex_enterprise.App.")
        context = {"sitemap": None}
        # Remove when reflex-enterprise drops support for < 0.8.25
        sitemap_none_unsupported = version.parse(
            rx.constants.Reflex.VERSION
        ) < version.parse("0.8.25.dev0")
        if sitemap_none_unsupported:
            console.warn(
                "Reflex version does not support sitemap=None in page context, OIDC routes will appear in /sitemap.xml. "
                "Upgrade to Reflex 0.8.25 or later to silence this warning."
            )
            context = {}
        app.add_page(
            cls.get_authentication_loading_page(),
            route=cls._authorization_code_endpoint(),
            on_load=cls.auth_callback,
            title=f"{cls.__provider__.title()} Auth Callback",
            context=context,
        )
        app.add_page(
            cls.get_authentication_loading_page(),
            route=cls._popup_login_endpoint(),
            on_load=[
                cls.set_from_popup(True),
                cls.redirect_to_login,
            ],
            title=f"{cls.__provider__.title()} Auth Initiator",
            context=context,
        )
        app.add_page(
            cls.get_authentication_popup_logout(),
            route=cls._popup_logout_endpoint(),
            on_load=[
                cls.set_from_popup(True),
                cls.redirect_to_logout,
            ],
            title=f"{cls.__provider__.title()} Auth Logout",
            context=context,
        )
