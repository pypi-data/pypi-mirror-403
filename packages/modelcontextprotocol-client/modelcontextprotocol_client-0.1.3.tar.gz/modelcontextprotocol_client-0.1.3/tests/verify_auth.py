
import asyncio
import pytest
from mcp.client.auth import OAuthClientProvider, OAuthClientMetadata, OAuthToken
from mcp.client.auth.provider import TokenStorage, OAuthClientInformationFull
from mcp.types.auth import OAuthMetadata, ProtectedResourceMetadata
from httpx import Request, Response, Auth
from unittest.mock import MagicMock, AsyncMock

# Mock Storage
class MockStorage(TokenStorage):
    def __init__(self):
        self.tokens = None
        self.client_info = None
    
    async def get_tokens(self): return self.tokens
    async def set_tokens(self, tokens): self.tokens = tokens
    async def get_client_info(self): return self.client_info
    async def set_client_info(self, info): self.client_info = info

@pytest.mark.asyncio
async def test_auth_provider_simple_flow():
    # Setup
    client_metadata = OAuthClientMetadata(redirect_uris=["http://localhost:8080/callback"])
    storage = MockStorage()
    
    # Mock Handlers
    redirect_handler = AsyncMock()
    callback_handler = AsyncMock(return_value=("auth_code", "state"))
    
    provider = OAuthClientProvider(
        server_url="http://test-server.com",
        client_metadata=client_metadata,
        storage=storage,
        redirect_handler=redirect_handler,
        callback_handler=callback_handler
    )
    
    # Pre-inject tokens to simulate "Already Authenticated" state for simple verification
    valid_token = OAuthToken(access_token="test_access_token", expires_in=3600)
    await storage.set_tokens(valid_token)
    provider.context.current_tokens = valid_token # Manually sync since we don't have load_tokens called automatically in __init__
    
    # Test Request
    request = Request("GET", "http://test-server.com/resource")
    
    # Run Flow
    flow_gen = provider.auth_flow(request)
    
    # First yield should be the request with headers injected
    authed_request = await anext(flow_gen)
    
    assert "Authorization" in authed_request.headers
    assert authed_request.headers["Authorization"] == "Bearer test_access_token"
    
    # Simulate server response 200 OK
    try:
        await flow_gen.asend(Response(200, request=request))
    except StopAsyncIteration:
        pass # Flow complete

if __name__ == "__main__":
    asyncio.run(test_auth_provider_simple_flow())
    print("Verification Script Completed Successfully")
