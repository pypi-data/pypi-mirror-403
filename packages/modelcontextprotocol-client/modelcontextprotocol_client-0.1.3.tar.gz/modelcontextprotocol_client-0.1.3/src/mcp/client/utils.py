from ..transport.stdio import StdioTransport,StdioServerParams
from ..transport.streamable_http import StreamableHTTPTransport
from ..transport.websocket import WebSocketTransport
from ..transport.sse import SSETransport
from ..transport.base import BaseTransport
from typing import Any

def create_transport_from_server_config(server_config:dict[str,Any])->BaseTransport:
    '''
    Create a transport based on the server configuration

    Args:
        server_config: The server configuration. May include:
            - url: The server URL (for HTTP-based transports)
            - command/args: Command and arguments (for stdio transport)
            - headers: Optional dict of HTTP headers (for authentication, etc.)
            - env: Optional dict of environment variables

    Returns:
        The transport instance for the server
    '''
    # Extract headers if provided (for authentication support)
    headers = server_config.get('headers', None)
    
    # Extract auth config
    auth_config = server_config.get('auth')
    auth_provider = None
    if auth_config:
        from .auth import OAuthClientProvider, OAuthClientMetadata
        
        # Simple In-Memory Storage for now 
        # TODO: Allow configuring persistent storage
        class MemoryTokenStorage:
             def __init__(self): self.tokens = None; self.client_info = None
             async def get_tokens(self): return self.tokens
             async def set_tokens(self, t): self.tokens = t
             async def get_client_info(self): return self.client_info
             async def set_client_info(self, i): self.client_info = i
        
        storage = MemoryTokenStorage()
        client_metadata = OAuthClientMetadata(**auth_config.get('client_metadata', {}))
        
        auth_provider = OAuthClientProvider(
            server_url=server_config.get('url'),
            client_metadata=client_metadata,
            storage=storage,
            # Handlers would need to be injected or default to console?
            # For a library, we can't assume console. 
            # This integration point is tricky without a UI/Callback mechanism.
            # We will leave handlers None which will raise if flow triggers.
            # This is acceptable for "Research/Prototype" phase.
        )
    
    # Valid transport types: 'sse', 'http', 'stdio', 'websocket'
    transport_type = server_config.get('transport')
    
    if transport_type == 'sse' or is_sse_transport(server_config):
        # We need to construct the HTTP client with auth if present
        return SSETransport(url=server_config['url'], headers=headers, auth=auth_provider)
    elif transport_type == 'stdio' or is_stdio_transport(server_config):
        params=StdioServerParams(**server_config)
        return StdioTransport(params=params)
    elif transport_type == 'http' or is_streamable_http_transport(server_config):
        return StreamableHTTPTransport(url=server_config['url'], headers=headers, auth=auth_provider)
    elif transport_type == 'websocket' or is_websocket_transport(server_config):
        return WebSocketTransport(url=server_config['url'], headers=headers)
    else:
        raise ValueError(f'Invalid server configuration: {server_config}')


def is_sse_transport(server_config:dict[str,Any])->bool:
    return 'url' in server_config and 'sse' in server_config.get('url')

def is_streamable_http_transport(server_config:dict[str,Any])->bool:
    return 'url' in server_config and 'mcp' in server_config.get('url')

def is_stdio_transport(server_config:dict[str,Any])->bool:
    return 'command' in server_config and 'args' in server_config

def is_websocket_transport(server_config:dict[str,Any])->bool:
    return 'url' in server_config and 'ws' in server_config.get('url')
    