
import base64
import hashlib
import logging
import secrets
import string
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import quote, urlencode, urljoin, urlparse

import anyio
import httpx
from pydantic import BaseModel, Field, ValidationError

from .exceptions import OAuthFlowError, OAuthTokenError
from .utils import (
    build_oauth_authorization_server_metadata_discovery_urls,
    build_protected_resource_metadata_discovery_urls,
    create_client_info_from_metadata_url,
    create_client_registration_request,
    create_oauth_metadata_request,
    extract_field_from_www_auth,
    extract_resource_metadata_from_www_auth,
    extract_scope_from_www_auth,
    get_client_metadata_scopes,
    handle_auth_metadata_response,
    handle_protected_resource_response,
    handle_registration_response,
    handle_token_response_scopes,
    is_valid_client_metadata_url,
    should_use_client_metadata_url,
)
from ...types.auth import (
    OAuthClientInformationFull,
    OAuthClientMetadata,
    OAuthMetadata,
    OAuthToken,
    ProtectedResourceMetadata,
)

logger = logging.getLogger(__name__)


class PKCEParameters(BaseModel):
    """PKCE (Proof Key for Code Exchange) parameters."""

    code_verifier: str = Field(..., min_length=43, max_length=128)
    code_challenge: str = Field(..., min_length=43, max_length=128)

    @classmethod
    def generate(cls) -> "PKCEParameters":
        """Generate new PKCE parameters."""
        code_verifier = "".join(secrets.choice(string.ascii_letters + string.digits + "-._~") for _ in range(128))
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
        return cls(code_verifier=code_verifier, code_challenge=code_challenge)


class TokenStorage(Protocol):
    """Protocol for token storage implementations."""

    async def get_tokens(self) -> OAuthToken | None:
        """Get stored tokens."""
        ...

    async def set_tokens(self, tokens: OAuthToken) -> None:
        """Store tokens."""
        ...

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        """Get stored client information."""
        ...

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        """Store client information."""
        ...


def calculate_token_expiry(expires_in: int | None) -> float | None:
    """Calculate absolute expiry time from expires_in seconds."""
    if expires_in is None:
        return None
    return time.time() + expires_in

def check_resource_allowed(requested_resource: str, configured_resource: str) -> bool:
    """Check if requested resource is allowed by configured resource (prefix match)."""
    return requested_resource.startswith(configured_resource)

def resource_url_from_server_url(server_url: str) -> str:
    """Get the resource URL from the server URL (usually same, but handles subtle normalization if needed)."""
    # For now assume server_url IS the resource url or close enough to use as is
    return server_url


@dataclass
class OAuthContext:
    """OAuth flow context."""

    server_url: str
    client_metadata: OAuthClientMetadata
    storage: TokenStorage
    redirect_handler: Callable[[str], Awaitable[None]] | None
    callback_handler: Callable[[], Awaitable[tuple[str, str | None]]] | None
    timeout: float = 300.0
    client_metadata_url: str | None = None

    # Discovered metadata
    protected_resource_metadata: ProtectedResourceMetadata | None = None
    oauth_metadata: OAuthMetadata | None = None
    auth_server_url: str | None = None
    protocol_version: str | None = None

    # Client registration
    client_info: OAuthClientInformationFull | None = None

    # Token management
    current_tokens: OAuthToken | None = None
    token_expiry_time: float | None = None

    # State
    lock: anyio.Lock = field(default_factory=anyio.Lock)

    def get_authorization_base_url(self, server_url: str) -> str:
        """Extract base URL by removing path component."""
        parsed = urlparse(server_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def update_token_expiry(self, token: OAuthToken) -> None:
        """Update token expiry time using shared util function."""
        self.token_expiry_time = calculate_token_expiry(token.expires_in)

    def is_token_valid(self) -> bool:
        """Check if current token is valid."""
        return bool(
            self.current_tokens
            and self.current_tokens.access_token
            and (not self.token_expiry_time or time.time() <= self.token_expiry_time)
        )

    def can_refresh_token(self) -> bool:
        """Check if token can be refreshed."""
        return bool(self.current_tokens and self.current_tokens.refresh_token and self.client_info)

    def clear_tokens(self) -> None:
        """Clear current tokens."""
        self.current_tokens = None
        self.token_expiry_time = None

    def get_resource_url(self) -> str:
        """Get resource URL for RFC 8707.

        Uses PRM resource if it's a valid parent, otherwise uses canonical server URL.
        """
        resource = resource_url_from_server_url(self.server_url)

        # If PRM provides a resource that's a valid parent, use it
        if self.protected_resource_metadata and self.protected_resource_metadata.resource:
            prm_resource = str(self.protected_resource_metadata.resource)
            if check_resource_allowed(requested_resource=resource, configured_resource=prm_resource):
                resource = prm_resource

        return resource

    def should_include_resource_param(self, protocol_version: str | None = None) -> bool:
        """Determine if the resource parameter should be included in OAuth requests.

        Returns True if:
        - Protected resource metadata is available, OR
        - MCP-Protocol-Version header is 2025-06-18 or later
        """
        # If we have protected resource metadata, include the resource param
        if self.protected_resource_metadata is not None:
            return True

        # If no protocol version provided, don't include resource param
        if not protocol_version:
            return False

        # Check if protocol version is 2025-06-18 or later
        # Version format is YYYY-MM-DD, so string comparison works
        return protocol_version >= "2025-06-18"

    def prepare_token_auth(
        self, data: dict[str, str], headers: dict[str, str] | None = None
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Prepare authentication for token requests.

        Args:
            data: The form data to send
            headers: Optional headers dict to update

        Returns:
            Tuple of (updated_data, updated_headers)
        """
        if headers is None:
            headers = {}  # pragma: no cover

        if not self.client_info:
            return data, headers  # pragma: no cover

        auth_method = self.client_info.token_endpoint_auth_method

        if auth_method == "client_secret_basic" and self.client_info.client_id and self.client_info.client_secret:
            # URL-encode client ID and secret per RFC 6749 Section 2.3.1
            encoded_id = quote(self.client_info.client_id, safe="")
            encoded_secret = quote(self.client_info.client_secret, safe="")
            credentials = f"{encoded_id}:{encoded_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
            # Don't include client_secret in body for basic auth
            data = {k: v for k, v in data.items() if k != "client_secret"}
        elif auth_method == "client_secret_post" and self.client_info.client_secret:
            # Include client_secret in request body
            data["client_secret"] = self.client_info.client_secret
        # For auth_method == "none", don't add any client_secret

        return data, headers


class OAuthClientProvider(httpx.Auth):
    """
    OAuth2 authentication for httpx.
    Handles OAuth flow with automatic client registration and token storage.
    """

    requires_response_body = True

    def __init__(
        self,
        server_url: str,
        client_metadata: OAuthClientMetadata,
        storage: TokenStorage,
        redirect_handler: Callable[[str], Awaitable[None]] | None = None,
        callback_handler: Callable[[], Awaitable[tuple[str, str | None]]] | None = None,
        timeout: float = 300.0,
        client_metadata_url: str | None = None,
    ):
        """Initialize OAuth2 authentication.

        Args:
            server_url: The MCP server URL.
            client_metadata: OAuth client metadata for registration.
            storage: Token storage implementation.
            redirect_handler: Handler for authorization redirects.
            callback_handler: Handler for authorization callbacks.
            timeout: Timeout for the OAuth flow.
            client_metadata_url: URL-based client ID. When provided and the server
                advertises client_id_metadata_document_supported=true, this URL will be
                used as the client_id instead of performing dynamic client registration.
                Must be a valid HTTPS URL with a non-root pathname.

        Raises:
            ValueError: If client_metadata_url is provided but not a valid HTTPS URL
                with a non-root pathname.
        """
        # Validate client_metadata_url if provided
        if client_metadata_url is not None and not is_valid_client_metadata_url(client_metadata_url):
            raise ValueError(
                f"client_metadata_url must be a valid HTTPS URL with a non-root pathname, got: {client_metadata_url}"
            )

        self.context = OAuthContext(
            server_url=server_url,
            client_metadata=client_metadata,
            storage=storage,
            redirect_handler=redirect_handler,
            callback_handler=callback_handler,
            timeout=timeout,
            client_metadata_url=client_metadata_url,
        )
        self._initialized = False

    async def _handle_protected_resource_response(self, response: httpx.Response) -> bool:
        """
        Handle protected resource metadata discovery response.

        Per SEP-985, supports fallback when discovery fails at one URL.

        Returns:
            True if metadata was successfully discovered, False if we should try next URL
        """
        metadata = await handle_protected_resource_response(response)
        if metadata:
            self.context.protected_resource_metadata = metadata
            if metadata.authorization_servers:  # pragma: no branch
                self.context.auth_server_url = str(metadata.authorization_servers[0])
            return True
        return False

    async def _perform_authorization(self) -> httpx.Request:
        """Perform the authorization flow."""
        auth_code, code_verifier = await self._perform_authorization_code_grant()
        token_request = await self._exchange_token_authorization_code(auth_code, code_verifier)
        return token_request

    async def _perform_authorization_code_grant(self) -> tuple[str, str]:
        """Perform the authorization redirect and get auth code."""
        if self.context.client_metadata.redirect_uris is None:
            raise OAuthFlowError("No redirect URIs provided for authorization code grant")  # pragma: no cover
        if not self.context.redirect_handler:
            raise OAuthFlowError("No redirect handler provided for authorization code grant")  # pragma: no cover
        if not self.context.callback_handler:
            raise OAuthFlowError("No callback handler provided for authorization code grant")  # pragma: no cover

        if self.context.oauth_metadata and self.context.oauth_metadata.authorization_endpoint:
            auth_endpoint = str(self.context.oauth_metadata.authorization_endpoint)  # pragma: no cover
        else:
            auth_base_url = self.context.get_authorization_base_url(self.context.server_url)
            auth_endpoint = urljoin(auth_base_url, "/authorize")

        if not self.context.client_info:
            raise OAuthFlowError("No client info available for authorization")  # pragma: no cover

        # Generate PKCE parameters
        pkce_params = PKCEParameters.generate()
        state = secrets.token_urlsafe(32)

        auth_params = {
            "response_type": "code",
            "client_id": self.context.client_info.client_id,
            "redirect_uri": str(self.context.client_metadata.redirect_uris[0]),
            "state": state,
            "code_challenge": pkce_params.code_challenge,
            "code_challenge_method": "S256",
        }

        # Only include resource param if conditions are met
        if self.context.should_include_resource_param(self.context.protocol_version):
            resource = self.context.get_resource_url()
            auth_params["resource"] = resource

        # Use scope selection strategy (WWW-Authenticate > PRM > None)
        # Note: We don't have access to the initial 401 response header here directly 
        # unless stored, but PRM scope takes specific precedence if available.
        # Ideally scope selection logic would be passed in or context updated.
        # For now, default to client metadata scope or PRM supported scopes.
        scope_to_use = get_client_metadata_scopes(
            None, # No access to WWW-Authenticate scope here easily without redesign
            self.context.protected_resource_metadata,
            self.context.oauth_metadata
        )
        if scope_to_use:
            auth_params["scope"] = scope_to_use
        elif self.context.client_metadata.scope:
            auth_params["scope"] = self.context.client_metadata.scope

        # Build authorization URL
        url_parts = list(urlparse(auth_endpoint))
        query = dict(item.split("=") for item in url_parts[4].split("&") if item) if url_parts[4] else {}
        query.update(auth_params)
        url_parts[4] = urlencode(query)
        auth_url = urlparse("")._replace(scheme=url_parts[0], netloc=url_parts[1], path=url_parts[2], params=url_parts[3], query=url_parts[4], fragment=url_parts[5]).geturl()

        # Trigger redirect
        await self.context.redirect_handler(auth_url)

        # Wait for callback
        code, returned_state = await self.context.callback_handler()

        if returned_state != state:
            raise OAuthFlowError("State mismatch in callback")

        return code, pkce_params.code_verifier

    async def _exchange_token_authorization_code(self, code: str, code_verifier: str) -> httpx.Request:
        """Create token exchange request."""
        if not self.context.oauth_metadata or not self.context.oauth_metadata.token_endpoint:
             # Fallback if discovery failed or didn't happen (unlikely in strict flow but possible)
             auth_base_url = self.context.get_authorization_base_url(self.context.server_url)
             token_endpoint = urljoin(auth_base_url, "/token")
        else:
             token_endpoint = str(self.context.oauth_metadata.token_endpoint)

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(self.context.client_metadata.redirect_uris[0]),
            "client_id": self.context.client_info.client_id,
            "code_verifier": code_verifier,
        }

        data, headers = self.context.prepare_token_auth(data)
        
        # httpx Request object to be sent by auth_flow generator
        return httpx.Request("POST", token_endpoint, data=data, headers=headers)

    async def auth_flow(self, request: httpx.Request) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """
        Execute the authentication flow.
        """
        # If we have valid tokens, inject and yield
        if self.context.is_token_valid():
            request.headers["Authorization"] = f"Bearer {self.context.current_tokens.access_token}"
            yield request
            return

        # Initial request (likely to fail with 401 if we are here and token is invalid/missing)
        # But we yield it first to let the server tell us we are unauthorized and provide discovery headers
        response = yield request

        if response.status_code == 401:
            # Check for WWW-Authenticate header to start discovery
            www_auth_res_metadata = extract_resource_metadata_from_www_auth(response)
            
            # Start Discovery
            auth_base_url = self.context.get_authorization_base_url(self.context.server_url)
            
            # Protected Resource Metadata Discovery
            disc_urls = build_protected_resource_metadata_discovery_urls(www_auth_res_metadata, self.context.server_url)
            
            metadata_found = False
            async with httpx.AsyncClient() as client:
                for url in disc_urls:
                    try:
                        resp = await client.get(url)
                        if await self._handle_protected_resource_response(resp):
                            metadata_found = True
                            break
                    except Exception as e:
                        logger.warning(f"Failed to fetch PRM from {url}: {e}")
                        continue
            
            # Authorization Server Metadata Discovery
            # Use auth_server_url if found in PRM, else fallback to server_url
            auth_server_url = self.context.auth_server_url
            asm_urls = build_oauth_authorization_server_metadata_discovery_urls(auth_server_url, self.context.server_url)
            
            async with httpx.AsyncClient() as client:
                for url in asm_urls:
                    try:
                        req = create_oauth_metadata_request(url)
                        resp = await client.send(req)
                        success, asm = await handle_auth_metadata_response(resp)
                        if success and asm:
                            self.context.oauth_metadata = asm
                            break
                        if not success:
                            break # Stop on non-retryable error
                    except Exception as e:
                        logger.warning(f"Failed to fetch ASM from {url}: {e}")
                        continue

            # Dynamic Client Registration
            # Skip if we have client info (restored from storage) or if using CIMD
            if not self.context.client_info:
                 should_cimd = should_use_client_metadata_url(self.context.oauth_metadata, self.context.client_metadata_url)
                 if should_cimd and self.context.client_metadata_url:
                     self.context.client_info = create_client_info_from_metadata_url(
                         self.context.client_metadata_url, 
                         self.context.client_metadata.redirect_uris
                     )
                 elif self.context.oauth_metadata:
                     # DCR
                     req = create_client_registration_request(
                         self.context.oauth_metadata, 
                         self.context.client_metadata, 
                         auth_base_url
                     )
                     async with httpx.AsyncClient() as client:
                         resp = await client.send(req)
                         self.context.client_info = await handle_registration_response(resp)
                         if self.context.storage:
                             await self.context.storage.set_client_info(self.context.client_info)
                 else:
                     raise OAuthRegistrationError("Cannot register client: Missing OAuth metadata")

            # Perform Authorization
            token_request = await self._perform_authorization()
            
            # Exchange Token
            async with httpx.AsyncClient() as client:
                token_response = await client.send(token_request)
                if token_response.status_code == 200:
                    tokens = await handle_token_response_scopes(token_response)
                    self.context.current_tokens = tokens
                    self.context.update_token_expiry(tokens)
                    if self.context.storage:
                        await self.context.storage.set_tokens(tokens)
                    
                    # Replay original request with new token
                    request.headers["Authorization"] = f"Bearer {tokens.access_token}"
                    yield request
                else:
                    raise OAuthTokenError(f"Token exchange failed: {token_response.status_code}")
