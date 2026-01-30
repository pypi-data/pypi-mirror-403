from mcp.types.json_rpc import (
    JSONRPCRequest,
    JSONRPCNotification,
    JSONRPCResponse,
    JSONRPCResultResponse,
    JSONRPCErrorResponse,
    JSONRPCError,
    JSONRPCMessage,
    Error,
    Method,
)
from mcp.transport.base import BaseTransport
from mcp.exception import MCPError
from mcp.logger import get_logger
from httpx import AsyncClient, Limits
from typing import Optional, Dict, Any
import asyncio
import json

logger = get_logger(__name__)


class StreamableHTTPTransport(BaseTransport):
    """
    HTTP transport supporting streaming JSON-RPC responses
    using asyncio.Future for one-shot request/response handling.
    """

    def __init__(self, url: str, headers: Optional[dict[str, str]] = None, auth: Optional[Any] = None):
        self.url = url
        self.headers = headers or {}
        self.auth = auth
        self.mcp_session_id = None
        self.protocol_version = None
        self.client: Optional[AsyncClient] = None
        self.listen_task: Optional[asyncio.Task] = None
        self.pending: Dict[str, asyncio.Future] = {}
        self._require_post_init = False

    async def connect(self):
        """Create an HTTP client and start the listener."""
        self.client = AsyncClient(
            timeout=10,
            headers=self.headers,
            auth=self.auth,
            limits=Limits(max_connections=10),
        )
        self.listen_task = asyncio.create_task(self.listen())

    async def send_response(self, response: JSONRPCResponse):
        """Send a JSON-RPC response."""
        if not self.client:
             raise MCPError(code=-1, message="HTTP client not connected")
        
        headers = {
            **self.headers,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.mcp_session_id:
            headers["mcp-session-id"] = self.mcp_session_id

        await self.client.post(self.url, headers=headers, json=response.model_dump(by_alias=True))

    async def listen(self, initial_request: Optional[JSONRPCMessage] = None):
        """
        Persistent stream listener for JSON-RPC responses.
        Keeps connection open and dispatches responses to pending Futures.
        """
        if not self.client:
             return

        headers = {
            **self.headers,
            "Accept": "application/json, text/event-stream",
        }
        if self.mcp_session_id:
            headers["mcp-session-id"] = self.mcp_session_id
        
        method = "GET"
        json_payload = None
        
        if initial_request:
            method = "POST"
            json_payload = initial_request.model_dump(by_alias=True, exclude_none=True)
            headers["Content-Type"] = "application/json"

    async def _process_stream(self, response):
        """Process SSE stream from a response."""
        try:
            if self.mcp_session_id is None:
                self.mcp_session_id = response.headers.get("mcp-session-id")

            buffer = bytearray()

            async for chunk in response.aiter_bytes():
                buffer.extend(chunk)
                
                if b'\n' in buffer:
                    parts = buffer.split(b'\n')
                    buffer = parts.pop()
                    
                    for part in parts:
                        if not part.strip():
                            continue
                        
                        # Handle SSE events
                        if part.startswith(b'data: '):
                            part = part[6:]
                        elif part.startswith(b'event: '):
                            continue
                        
                        try:
                            content = json.loads(part.decode(errors="ignore"))
                        except json.JSONDecodeError:
                            continue

                        if "result" in content:
                            msg_id = content.get("id")
                            message = JSONRPCResultResponse.model_validate(content)
                            if msg_id in self.pending:
                                fut = self.pending.pop(msg_id)
                                if not fut.done():
                                    fut.set_result(message)

                        elif "method" in content:
                            message = JSONRPCRequest.model_validate(content)
                            response_msg = await self.handle_request(message)
                            await self.send_response(response_msg)

                        elif "error" in content:
                            msg_id = content.get("id")
                            err = Error.model_validate(content["error"])
                            message = JSONRPCErrorResponse(
                                id=msg_id,
                                error=err,
                            )
                            if msg_id in self.pending:
                                fut = self.pending.pop(msg_id)
                                if not fut.done():
                                    fut.set_result(message)
        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
        finally:
            await response.aclose()


    async def listen(self, initial_request: Optional[JSONRPCMessage] = None):
        """
        Persistent stream listener for JSON-RPC responses.
        """
        if not self.client:
             return

        headers = {
            **self.headers,
            "Accept": "application/json, text/event-stream",
        }
        if self.mcp_session_id:
            headers["mcp-session-id"] = self.mcp_session_id
        
        method = "GET"
        json_payload = None
        
        if initial_request:
            method = "POST"
            json_payload = initial_request.model_dump(by_alias=True, exclude_none=True)
            headers["Content-Type"] = "application/json"

        try:
            request = self.client.build_request(method, self.url, headers=headers, json=json_payload, timeout=None)
            response = await self.client.send(request, stream=True)
            
            if method == "GET" and response.status_code == 405:
                # Server requires POST (likely Remote MCP pattern)
                self._require_post_init = True
                await response.aclose()
                return

            await self._process_stream(response)

        except Exception as e:
            logger.error(f"Listen error: {e}", exc_info=True)

    async def send_request(self, request: JSONRPCMessage) -> JSONRPCResponse:
        """
        Send a JSON-RPC request and await its response via Future.
        """
        if not self.client:
            raise MCPError(code=-1, message="HTTP client not connected")

        future = asyncio.get_event_loop().create_future()
        self.pending[request.id] = future

        # Handle Post-Init Flow
        if request.method == "initialize" and (self._require_post_init or (self.listen_task and self.listen_task.done())):
             # If listen task is done (likely due to 405), and we need post init
             # Restart listen with this request
             self.listen_task = asyncio.create_task(self.listen(initial_request=request))
        else:
            headers = {
                **self.headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            if self.mcp_session_id:
                headers["mcp-session-id"] = self.mcp_session_id
            if self.protocol_version:
                headers["mcp-protocol-version"] = self.protocol_version

            req = self.client.build_request("POST", self.url, headers=headers, json=request.model_dump(by_alias=True, exclude_none=True), timeout=None)
            response_obj = await self.client.send(req, stream=True)
            
            # Check content type for SSE upgrade
            ct = response_obj.headers.get("Content-Type", "")
            if "text/event-stream" in ct:
                # We accidentally started the stream.
                if self.listen_task and not self.listen_task.done():
                    self.listen_task.cancel()
                self._require_post_init = True
                self.listen_task = asyncio.create_task(self._process_stream(response_obj))
                # Do NOT wait for response_obj read, wait for pending future
            else:
                try:
                    await asyncio.wait_for(response_obj.aread(), timeout=60.0)
                    
                    # Check if response contains the result directly
                    if response_obj.status_code in (200, 202):
                        try:
                            content = response_obj.json()
                            if isinstance(content, dict) and content.get("id") == request.id:
                                self.pending.pop(request.id, None)
                                if "error" in content:
                                    err = Error.model_validate(content["error"])
                                    return JSONRPCErrorResponse(id=request.id, error=err)
                                return JSONRPCResultResponse.model_validate(content)
                        except json.JSONDecodeError:
                            pass
                    elif response_obj.status_code >= 400:
                        self.pending.pop(request.id, None)
                        raise MCPError(code=response_obj.status_code, message=f"HTTP Error: {response_obj.text}")
                finally:
                    await response_obj.aclose()

        try:
            response = await asyncio.wait_for(future, timeout=30)
        except asyncio.TimeoutError:
            self.pending.pop(request.id, None)
            raise MCPError(code=-1, message="Request timed out")

        if isinstance(response, JSONRPCErrorResponse):
            raise MCPError(code=response.error.code, message=response.error.message)

        # If initialize method, capture protocol version
        if request.method == Method.INITIALIZE and isinstance(response, JSONRPCResponse):
            self.protocol_version = response.result.get("protocolVersion")

        return response

    async def send_notification(self, notification: JSONRPCMessage):
        """Send a fire-and-forget notification."""
        if not self.client:
            raise MCPError(code=-1, message="HTTP client not connected")

        headers = {
            **self.headers,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        if self.mcp_session_id:
            headers["mcp-session-id"] = self.mcp_session_id

        await self.client.post(self.url, headers=headers, json=notification.model_dump(by_alias=True))

    async def disconnect(self):
        """Gracefully close the session and cancel pending Futures."""
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
            finally:
                self.listen_task = None

        if self.client:
            headers = {
                **self.headers,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self.mcp_session_id:
                headers["mcp-session-id"] = self.mcp_session_id
            try:
                await self.client.delete(self.url, headers=headers)
            finally:
                await self.client.aclose()
                self.client = None

        # Cancel pending futures
        for fut in self.pending.values():
            if not fut.done():
                fut.cancel()
        self.pending.clear()

        self.mcp_session_id = None
        self.protocol_version = None
