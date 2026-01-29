from ..types.capabilities import ClientCapabilities, ClientRootsCapability, ClientSamplingCapability, ClientElicitationCapability
from ..types.json_rpc import JSONRPCRequest, JSONRPCNotification, Method, JSONRPCMessage, JSONRPCResponse
from ..types.resources import (
    ListResourcesRequest, ListResourcesResult,
    ReadResourceRequest, ReadResourceRequestParams, ReadResourceResult,
    ListResourceTemplatesRequest, ListResourceTemplatesResult,
    SubscribeRequest, SubscribeRequestParams,
    UnsubscribeRequest, UnsubscribeRequestParams
)
from ..types.initialize import InitializeResult, InitializeRequestParams, InitializeRequest
from ..types.tools import (
    Tool, CallToolRequest, CallToolRequestParams, CallToolResult,
    ListToolsRequest, ListToolsResult
)
from ..types.prompts import (
    Prompt, GetPromptResult, GetPromptRequest, GetPromptRequestParams,
    ListPromptsRequest, ListPromptsResult
)
from ..types.completion import CompleteRequest, CompleteRequestParams, CompleteResult
from ..types.elicitation import ElicitResult
from ..transport.base import BaseTransport
from ..types.sampling import CreateMessageResult
from ..types.info import Implementation
from ..types.common import RequestParams, PaginatedRequestParams
from ..types.logging import SetLevelRequest, SetLevelRequestParams
from ..types.ping import PingRequest
from ..types.notification import InitializedNotification
from ..types.roots import RootsListChangedNotification
from typing import Optional, Any
from uuid import uuid4

class Session:
    def __init__(self, transport: BaseTransport, client_info: Implementation) -> None:
        self.transport = transport
        self.client_info = client_info
        self.initialize_result: Optional[InitializeResult] = None

    async def connect(self) -> None:
        await self.transport.connect()

    def get_initialize_result(self) -> InitializeResult:
        return self.initialize_result

    async def initialize(self) -> InitializeResult:
        PROTOCOL_VERSION = "2024-11-05"
        
        # Capability Mapping
        # Roots
        roots = ClientRootsCapability(listChanged=True) if self.transport.callbacks.get("list_roots") else None
        
        # Sampling
        # Note: ClientSamplingCapability requires context/tools objects, defaulting to None/empty if implied supported
        # If callback exists, imply support?
        # Schema says empty object implies support for properties? No, they are Specific capabilities.
        # For now, if sampling callback exists, we declare empty capability object which implies support.
        sampling = ClientSamplingCapability() if self.transport.callbacks.get("sampling") else None
        
        # Elicitation
        # Similarly for elicitation
        elicitation = ClientElicitationCapability() if self.transport.callbacks.get("elicitation") else None

        params = InitializeRequestParams(
            clientInfo=self.client_info,
            capabilities=ClientCapabilities(
                roots=roots,
                sampling=sampling,
                elicitation=elicitation
            ),
            protocolVersion=PROTOCOL_VERSION
        )
        
        request = InitializeRequest(
            id=str(uuid4()),
            params=params
        )
        
        response = await self.transport.send_request(request=request)
        
        notification = InitializedNotification()
        await self.transport.send_notification(notification=notification)
        
        self.initialize_result = InitializeResult.model_validate(response.result)
        return self.initialize_result
    
    async def ping(self) -> bool:
        request = PingRequest(id=str(uuid4()))
        response = await self.transport.send_request(request=request)
        return response is not None

    async def list_prompts(self, params: Optional[PaginatedRequestParams] = None) -> ListPromptsResult:
        """List all prompts"""
        request = ListPromptsRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return ListPromptsResult.model_validate(response.result)
    
    async def get_prompt(self, params: GetPromptRequestParams) -> GetPromptResult:
        """Get a prompt"""
        request = GetPromptRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return GetPromptResult.model_validate(response.result)
    
    async def list_resources(self, params: Optional[PaginatedRequestParams] = None) -> ListResourcesResult:
        """List all resources"""
        request = ListResourcesRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return ListResourcesResult.model_validate(response.result)
    
    async def read_resource(self, params: ReadResourceRequestParams) -> ReadResourceResult:
        """Read a resource"""
        request = ReadResourceRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return ReadResourceResult.model_validate(response.result)
    
    async def resources_templates_list(self, params: Optional[PaginatedRequestParams] = None) -> ListResourceTemplatesResult:
        request = ListResourceTemplatesRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return ListResourceTemplatesResult.model_validate(response.result)
    
    async def resources_subscribe(self, params: SubscribeRequestParams) -> None:
        request = SubscribeRequest(
            id=str(uuid4()),
            params=params
        )
        await self.transport.send_request(request=request)

    async def resources_unsubscribe(self, params: UnsubscribeRequestParams) -> None:
        request = UnsubscribeRequest(
            id=str(uuid4()),
            params=params
        )
        await self.transport.send_request(request=request)
    
    async def list_tools(self, params: Optional[PaginatedRequestParams] = None) -> ListToolsResult:
        """List all tools"""
        request = ListToolsRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return ListToolsResult.model_validate(response.result)
    
    async def call_tool(self, params: CallToolRequestParams) -> CallToolResult:
        """Call a tool"""
        request = CallToolRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return CallToolResult.model_validate(response.result)
    
    async def roots_list_changed(self) -> None:
        notification = RootsListChangedNotification()
        await self.transport.send_notification(notification=notification)

    async def completion_complete(self, params: CompleteRequestParams) -> CompleteResult:
        request = CompleteRequest(
            id=str(uuid4()),
            params=params
        )
        response = await self.transport.send_request(request=request)
        return CompleteResult.model_validate(response.result)

    async def logging_set_level(self, params: SetLevelRequestParams) -> None:
        request = SetLevelRequest(
            id=str(uuid4()),
            params=params
        )
        await self.transport.send_request(request=request)

    async def shutdown(self) -> None:
        await self.transport.disconnect()
    
    @property
    def server_info(self) -> Optional[Implementation]:
        """Get server information from initialize result"""
        return self.initialize_result.serverInfo if self.initialize_result else None
    
    @property
    def server_capabilities(self) -> Optional[Any]:
        """Get server capabilities from initialize result"""
        return self.initialize_result.capabilities if self.initialize_result else None