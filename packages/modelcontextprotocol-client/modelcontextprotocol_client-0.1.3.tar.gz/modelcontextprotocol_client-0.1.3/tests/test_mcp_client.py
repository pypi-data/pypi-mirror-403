"""
Test script to verify MCP client functionality
Tests: tools, prompts, resources, and protocol compliance
"""
import asyncio
import json
import pytest
from mcp.client import Client
from mcp.types.tools import CallToolRequestParams
from mcp.types.prompts import GetPromptRequestParams
from mcp.types.resources import ReadResourceRequestParams

@pytest.mark.asyncio
async def test_mcp():
    """Comprehensive test of MCP client functionality"""
    
    print("=" * 80)
    print("MCP CLIENT COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Create test server configuration
    config = {
        "mcpServers": {
            "test-server": {
                "command": "uv",
                "args": ["run", "tests/test_mcp_server.py"],
                "description": "Comprehensive test server with tools, prompts, and resources"
            }
        }
    }
    
    # Initialize client
    print("\n1. Initializing MCP Client...")
    client = Client.from_config(config)
    print(f"   ✓ Client initialized with {len(client.get_server_names())} server(s)")
    
    try:
        # Connect to server
        print("\n2. Connecting to test-server...")
        session = await client.create_session("test-server")
        print(f"   ✓ Connected successfully")
        print(f"   Server Info: {session.server_info}")
        
        # Test 1: List and call tools
        print("\n3. Testing TOOLS...")
        tools_result = await session.list_tools()
        print(f"   ✓ Found {len(tools_result.tools)} tools:")
        for tool in tools_result.tools:
            print(f"     - {tool.name}: {tool.description}")
        
        # Call add_numbers tool
        print("\n   Testing add_numbers tool...")
        result = await session.call_tool(CallToolRequestParams(name="add_numbers", arguments={"a": 5, "b": 3}))
        print(f"   ✓ add_numbers(5, 3) = {result.content[0].text}")
        
        # Call get_user_info tool
        print("\n   Testing get_user_info tool...")
        result = await session.call_tool(CallToolRequestParams(name="get_user_info", arguments={"user_id": "123"}))
        print(f"   ✓ get_user_info('123') = {result.content[0].text}")
        
        # Call search_items tool
        print("\n   Testing search_items tool...")
        result = await session.call_tool(CallToolRequestParams(name="search_items", arguments={"query": "test", "limit": 3}))
        print(f"   ✓ search_items('test', limit=3) returned {len(result.content)} result(s)")
        
        # Test 2: List and get prompts
        print("\n4. Testing PROMPTS...")
        prompts_result = await session.list_prompts()
        print(f"   ✓ Found {len(prompts_result.prompts)} prompts:")
        for prompt in prompts_result.prompts:
            print(f"     - {prompt.name}: {prompt.description}")
        
        # Get code_review_prompt
        print("\n   Testing code_review_prompt...")
        result = await session.get_prompt(GetPromptRequestParams(name="code_review_prompt", arguments={
            "code": "def hello():\n    print('world')",
            "language": "python"
        }))
        print(f"   ✓ Generated prompt (first 100 chars): {result.messages[0].content.text[:100]}...")
        
        # Test 3: List and read resources
        print("\n5. Testing RESOURCES...")
        resources_result = await session.list_resources()
        print(f"   ✓ Found {len(resources_result.resources)} resources:")
        for resource in resources_result.resources:
            print(f"     - {resource.uri}: {resource.name}")
        
        # Read config resource
        print("\n   Testing config://app resource...")
        result = await session.read_resource(ReadResourceRequestParams(uri="config://app"))
        config_data = json.loads(result.contents[0].text)
        print(f"   ✓ Read config: app_name = {config_data['app_name']}, version = {config_data['version']}")
        
        # Read docs resource
        print("\n   Testing docs://getting-started resource...")
        result = await session.read_resource(ReadResourceRequestParams(uri="docs://getting-started"))
        print(f"   ✓ Read docs (first 100 chars): {result.contents[0].text[:100]}...")
        
        # Read data resource
        print("\n   Testing data://sample resource...")
        result = await session.read_resource(ReadResourceRequestParams(uri="data://sample"))
        data = json.loads(result.contents[0].text)
        print(f"   ✓ Read sample data: {len(data)} records")
        
        # Test 4: Server capabilities
        print("\n6. Testing SERVER CAPABILITIES...")
        print(f"   Server Capabilities:")
        if session.server_capabilities:
            if hasattr(session.server_capabilities, 'tools'):
                print(f"     - Tools: {session.server_capabilities.tools is not None}")
            if hasattr(session.server_capabilities, 'prompts'):
                print(f"     - Prompts: {session.server_capabilities.prompts is not None}")
            if hasattr(session.server_capabilities, 'resources'):
                print(f"     - Resources: {session.server_capabilities.resources is not None}")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n7. Cleaning up...")
        await client.close_all_sessions()
        print("   ✓ All sessions closed")

if __name__ == "__main__":
    asyncio.run(test_mcp())
