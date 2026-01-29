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
    
    # Valid transport types: 'sse', 'http', 'stdio', 'websocket'
    transport_type = server_config.get('transport')
    
    if transport_type == 'sse' or is_sse_transport(server_config):
        return SSETransport(url=server_config['url'], headers=headers)
    elif transport_type == 'stdio' or is_stdio_transport(server_config):
        params=StdioServerParams(**server_config)
        return StdioTransport(params=params)
    elif transport_type == 'http' or is_streamable_http_transport(server_config):
        return StreamableHTTPTransport(url=server_config['url'], headers=headers)
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
    