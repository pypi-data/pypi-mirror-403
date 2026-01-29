"""
Advanced Test Client for MCP
Tests: Sampling, Elicitation, Roots, and Notifications
"""
import asyncio
import json
from src.mcp.client import MCPClient
from src.mcp.types.sampling import CreateMessageResult, TextContent as SamplingTextContent
from src.mcp.types.elicitation import ElicitResult
from src.mcp.types.roots import ListRootsResult, Root

async def sampling_handler(params):
    print(f"   [Sampling Request] Message: {params.messages[0].content.text}")
    # Simulate an AI response
    return CreateMessageResult(
        role="assistant",
        content=SamplingTextContent(type="text", text="The answer is 4 (simulated)"),
        model="gpt-4",
        stopReason="endTurn"
    )

async def elicitation_handler(params):
    print(f"   [Elicitation Request] Message: {params.message}")
    return ElicitResult(action="accept", content={"name": "John Doe"})

async def list_roots_handler(params):
    print(f"   [List Roots Request] Server asked for roots")
    return ListRootsResult(roots=[Root(uri="file:///d:/Projects/Process", name="Project Root")])

async def notification_handler(name):
    async def handler():
        print(f"   [Notification] {name} list changed!")
    return handler

async def resource_updated_handler(params):
    print(f"   [Notification] Resource updated: {params.get('uri')}")

async def run_advanced_test():
    print("=" * 80)
    print("MCP CLIENT ADVANCED FEATURES TEST")
    print("=" * 80)
    
    config = {
        "mcpServers": {
            "advanced-server": {
                "command": "python",
                "args": ["advanced_test_server.py"],
                "description": "Advanced test server for sampling and notifications"
            }
        }
    }
    
    # Initialize client with all callbacks
    client = MCPClient.from_config(
        config,
        sampling_callback=sampling_handler,
        elicitation_callback=elicitation_handler,
        list_roots_callback=list_roots_handler,
        tools_list_changed_callback=await notification_handler("Tools"),
        prompts_list_changed_callback=await notification_handler("Prompts"),
        resources_list_changed_callback=await notification_handler("Resources"),
        roots_list_changed_callback=await notification_handler("Roots"),
        resource_updated_callback=resource_updated_handler
    )
    
    try:
        print("\n1. Connecting to advanced-server...")
        session = await client.create_session("advanced-server")
        print("   ✓ Connected")
        
        # Test Sampling
        print("\n2. Testing SAMPLING (Server-to-Client Request)...")
        result = await session.call_tool("trigger_sampling")
        print(f"   ✓ Tool Result: {result.content[0].text}")
        
        # Test Elicitation
        print("\n3. Testing ELICITATION (Server-to-Client Request)...")
        result = await session.call_tool("trigger_elicitation")
        print(f"   ✓ Tool Result: {result.content[0].text}")
        
        # Test Roots
        print("\n4. Testing ROOTS (Server-to-Client Request)...")
        result = await session.call_tool("trigger_list_roots")
        print(f"   ✓ Tool Result: {result.content[0].text}")
        
        # Test Notifications
        print("\n5. Testing NOTIFICATIONS (List Changed)...")
        result = await session.call_tool("trigger_notifications")
        print(f"   ✓ Tool Result: {result.content[0].text}")
        
        # Test Subscriptions
        print("\n6. Testing SUBSCRIPTIONS...")
        from mcp.types.resources import SubscribeRequestParams
        await session.resources_subscribe(SubscribeRequestParams(uri="test://resource"))
        print("   ✓ Subscribed to test://resource")
        
        # Test Resource Updates (Manual Trigger)
        print("\n7. Testing RESOURCE UPDATES (Manual Trigger)...")
        result = await session.call_tool("trigger_resource_update")
        print(f"   ✓ Tool Result: {result.content[0].text}")
        
        # Wait a moment for notifications to arrive (though they are sequential in this test server)
        await asyncio.sleep(1)
        
        print("\n" + "=" * 80)
        print("ADVANCED TESTS COMPLETED ✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(run_advanced_test())
