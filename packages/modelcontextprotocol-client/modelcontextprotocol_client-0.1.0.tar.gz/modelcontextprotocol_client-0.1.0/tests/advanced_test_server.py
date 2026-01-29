"""
Manual MCP Server for Advanced Features Testing
Handles: Sampling, Elicitation, Roots, and Notifications
"""
import sys
import json
import asyncio
from uuid import uuid4

async def send_json(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()

async def advanced_test_server():
    # 1. Handle Initialization
    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    if not line: return
    init_request = json.loads(line)
    
    # Send Initialize Result
    await send_json({
        "jsonrpc": "2.0",
        "id": init_request["id"],
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "sampling": {},
                "elicitation": {},
                "prompts": {},
                "resources": {"subscribe": True},
                "tools": {}
            },
            "serverInfo": {"name": "advanced-test-server", "version": "1.0.0"}
        }
    })
    
    # Receive Initialized Notification
    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    
    # Loop for requests
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line: break
        
        request = json.loads(line)
        method = request.get("method")
        
        if method == "resources/list":
            await send_json({
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "resources": [{"uri": "test://resource", "name": "Test Resource"}]
                }
            })

        elif method == "resources/subscribe":
            await send_json({
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {}
            })
            # Trigger an immediate update
            await send_json({
                "jsonrpc": "2.0",
                "method": "notifications/resources/updated",
                "params": {"uri": "test://resource"}
            })

        elif method == "resources/unsubscribe":
            await send_json({
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {}
            })

        elif method == "tools/list":
            await send_json({
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "tools": [
                        {"name": "trigger_sampling", "description": "Ask client to sample a message"},
                        {"name": "trigger_elicitation", "description": "Ask client to elicit info"},
                        {"name": "trigger_list_roots", "description": "Ask client for its roots"},
                        {"name": "trigger_notifications", "description": "Send list_changed notifications"},
                        {"name": "trigger_resource_update", "description": "Send resource update notification"}
                    ]
                }
            })
            
        elif method == "tools/call":
            tool_name = request["params"]["name"]
            
            if tool_name == "trigger_sampling":
                # Server-to-Client Request: sampling/createMessage
                sampling_id = str(uuid4())
                await send_json({
                    "jsonrpc": "2.0",
                    "id": sampling_id,
                    "method": "sampling/createMessage",
                    "params": {
                        "messages": [{"role": "user", "content": {"type": "text", "text": "What is 2+2?"}}],
                        "maxTokens": 100
                    }
                })
                # Wait for client response to sampling
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                sampling_response = json.loads(line)
                
                await send_json({
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [{"type": "text", "text": f"Client sampled: {sampling_response['result']['content']['text']}"}]
                    }
                })
                
            elif tool_name == "trigger_elicitation":
                # Server-to-Client Request: elicitation/create
                elicit_id = str(uuid4())
                await send_json({
                    "jsonrpc": "2.0",
                    "id": elicit_id,
                    "method": "elicitation/create",
                    "params": {
                        "message": "Enter your name:",
                        "mode": "form",
                        "requestedSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"}
                            },
                            "required": ["name"]
                        }
                    }
                })
                # Wait for client response
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                elicit_response = json.loads(line)
                
                await send_json({
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [{"type": "text", "text": f"Client elicited: {elicit_response['result']['content']['name']} with action {elicit_response['result']['action']}"}]
                    }
                })

            elif tool_name == "trigger_list_roots":
                # Server-to-Client Request: roots/list
                roots_id = str(uuid4())
                await send_json({
                    "jsonrpc": "2.0",
                    "id": roots_id,
                    "method": "roots/list",
                    "params": {}
                })
                # Wait for client response
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                roots_response = json.loads(line)
                
                roots_count = len(roots_response['result']['roots'])
                await send_json({
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [{"type": "text", "text": f"Client has {roots_count} roots"}]
                    }
                })
                
            elif tool_name == "trigger_notifications":
                # Notifications: list_changed
                await send_json({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
                await send_json({"jsonrpc": "2.0", "method": "notifications/prompts/list_changed"})
                await send_json({"jsonrpc": "2.0", "method": "notifications/resources/list_changed"})
                await send_json({"jsonrpc": "2.0", "method": "notifications/roots/list_changed"})
                
                await send_json({
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"content": [{"type": "text", "text": "Sent 4 list_changed notifications"}]}
                })

            elif tool_name == "trigger_resource_update":
                # Notification: resources/updated
                await send_json({
                    "jsonrpc": "2.0", 
                    "method": "notifications/resources/updated",
                    "params": {"uri": "test://resource"}
                })
                
                await send_json({
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"content": [{"type": "text", "text": "Sent resource update notification"}]}
                })

if __name__ == "__main__":
    asyncio.run(advanced_test_server())
