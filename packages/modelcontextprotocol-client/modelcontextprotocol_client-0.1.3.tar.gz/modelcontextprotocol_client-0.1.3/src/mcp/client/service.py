from .utils import create_transport_from_server_config
from ..types.elicitation import ElicitationFn
from ..types.sampling import SamplingFn
from ..types.roots import ListRootsFn
from ..types.info import Implementation
from typing import Callable, Optional
from .session import Session
from typing import Any
from uuid import uuid4
import json

import os
import re

class Client:
    client_info = Implementation(name="MCP Client", version="0.1.0")
    
    def __init__(self, 
                 config: dict[str, dict[str, Any]] = {}, 
                 sampling_callback: Optional[SamplingFn] = None, 
                 elicitation_callback: Optional[ElicitationFn] = None, 
                 list_roots_callback: Optional[ListRootsFn] = None, 
                 roots_list_changed_callback: Optional[Callable] = None,
                 logging_callback: Optional[Callable] = None,
                 resources_list_changed_callback: Optional[Callable] = None,
                 resource_updated_callback: Optional[Callable] = None,
                 prompts_list_changed_callback: Optional[Callable] = None,
                 tools_list_changed_callback: Optional[Callable] = None
                 ) -> None:
        self.servers = config.get("mcpServers", {})
        self.sampling_callback = sampling_callback
        self.list_roots_callback = list_roots_callback
        self.roots_list_changed_callback = roots_list_changed_callback
        self.elicitation_callback = elicitation_callback
        self.logging_callback = logging_callback
        self.resources_list_changed_callback = resources_list_changed_callback
        self.resource_updated_callback = resource_updated_callback
        self.prompts_list_changed_callback = prompts_list_changed_callback
        self.tools_list_changed_callback = tools_list_changed_callback
        self.sessions: dict[str, Session] = {}
        
    @classmethod
    def from_config(cls, 
                    config: dict[str, dict[str, Any]], 
                    sampling_callback: Optional[Callable] = None, 
                    elicitation_callback: Optional[Callable] = None, 
                    list_roots_callback: Optional[Callable] = None, 
                    roots_list_changed_callback: Optional[Callable] = None,
                    logging_callback: Optional[Callable] = None,
                    resources_list_changed_callback: Optional[Callable] = None,
                    resource_updated_callback: Optional[Callable] = None,
                    prompts_list_changed_callback: Optional[Callable] = None,
                    tools_list_changed_callback: Optional[Callable] = None
                    ) -> 'Client':
        return cls(config=config, 
                   sampling_callback=sampling_callback, 
                   elicitation_callback=elicitation_callback, 
                   list_roots_callback=list_roots_callback, 
                   roots_list_changed_callback=roots_list_changed_callback,
                   logging_callback=logging_callback,
                   resources_list_changed_callback=resources_list_changed_callback,
                   resource_updated_callback=resource_updated_callback,
                   prompts_list_changed_callback=prompts_list_changed_callback,
                   tools_list_changed_callback=tools_list_changed_callback
                   )
    
    @classmethod
    def from_config_file(cls, config_file_path: str) -> 'Client':
        with open(config_file_path) as f:
            config = json.load(f)
            
        def expand_env_vars(obj):
            if isinstance(obj, dict):
                return {k: expand_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [expand_env_vars(v) for v in obj]
            elif isinstance(obj, str):
                # Replace ${VAR} with value from os.environ, defaulting to original string if not found
                return re.sub(r'\$\{([a-zA-Z0-9_]+)\}', lambda m: os.getenv(m.group(1), m.group(0)), obj)
            else:
                return obj
                
        config = expand_env_vars(config)
        return cls(config=config)
    
    def get_server_names(self) -> list[str]:
        return list(self.servers.keys())
    
    def get_servers_info(self)->list[dict[str,Any]]:
        return [{
            'id':str(uuid4()),
            'name':name,
            'description':config.get("description",""),
            'status':self.is_connected(name)
        } for name,config in self.servers.items()]

    def to_config_file(self, config_file_path: str) -> None:
        with open(config_file_path, "w") as f:
            json.dump(self.to_config(), f, indent=4)

    def to_config(self) -> dict[str, dict[str, Any]]:
        return {"mcpServers": self.servers}

    def add_server(self, name: str, config: dict[str, Any], auto_connect: bool = False) -> None:
        self.servers[name] = config
        if auto_connect:
            self.create_session(name)

    def remove_server(self, name: str) -> None:
        if self.get_session(name):
            self.close_session(name)
        del self.servers[name]

    async def create_session(self, name: str) -> Session:
        if not self.servers:
            raise Exception("No MCP servers available")
        if name not in self.servers:
            raise ValueError(f"{name} not found")
        
        # Check if an active session already exists
        if name in self.sessions:
            # You might want to verify it's actually pingable, but for now checking existence is checking "intent"
            return self.sessions[name]

        server_config = self.servers.get(name)
        
        # TODO: Here we could initialize OAuthClientProvider if complex auth is needed
        # For now, we rely on the transport factory to handle simple headers or
        # we can inject the auth provider into the config passed to the factory.
        
        transport = create_transport_from_server_config(server_config=server_config)
        transport.attach_callbacks({
            'sampling': self.sampling_callback,
            'elicitation': self.elicitation_callback,
            'list_roots': self.list_roots_callback,
            'roots_list_changed': self.roots_list_changed_callback,
            'logging': self.logging_callback,
            'resources_list_changed': self.resources_list_changed_callback,
            'resource_updated': self.resource_updated_callback,
            'prompts_list_changed': self.prompts_list_changed_callback,
            'tools_list_changed': self.tools_list_changed_callback
        })
        session = Session(transport=transport, client_info=self.client_info)
        await session.connect()
        await session.initialize()
        self.sessions[name] = session
        return session
    
    def is_connected(self, server_name: str) -> bool:
        return server_name in self.sessions
    
    def get_session(self, name: str) -> Session | None:
        return self.sessions.get(name)
    
    def get_all_sessions(self) -> dict[str, Session]:
        return self.sessions
    
    async def close_session(self, name: str) -> None:
        if not self.is_connected(name):
            raise ValueError(f"Session {name} not found")
        session = self.sessions.get(name)
        await session.shutdown()
        del self.sessions[name]

    async def create_all_sessions(self) -> None:
        for name in self.servers:
            await self.create_session(name=name)

    async def close_all_sessions(self) -> None:
        for name in list(self.sessions.keys()):
            await self.close_session(name=name)
    

        

