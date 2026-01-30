"""
Comprehensive Test MCP Server
This server implements tools, prompts, and resources to test MCP client functionality.
"""
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("test-server")

# ============================================================================
# TOOLS - Functions that can be called by the client
# ============================================================================

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.tool()
def get_user_info(user_id: str) -> dict:
    """Get information about a user"""
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "status": "active"
    }

@mcp.tool()
def search_items(query: str, limit: int = 10) -> list:
    """Search for items matching a query"""
    # Simulate search results
    return [
        {"id": i, "title": f"Item {i} matching '{query}'", "score": 100 - i}
        for i in range(1, min(limit + 1, 11))
    ]

# ============================================================================
# PROMPTS - Pre-defined prompt templates
# ============================================================================

@mcp.prompt()
def code_review_prompt(code: str, language: str = "python") -> str:
    """Generate a code review prompt"""
    return f"""Please review the following {language} code:

```{language}
{code}
```

Provide feedback on:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Best practices
"""

@mcp.prompt()
def summarize_prompt(text: str, max_words: int = 100) -> str:
    """Generate a text summarization prompt"""
    return f"""Summarize the following text in no more than {max_words} words:

{text}

Summary:"""

# ============================================================================
# RESOURCES - Static or dynamic content that can be read
# ============================================================================

@mcp.resource("config://app")
def get_app_config() -> str:
    """Get application configuration"""
    return """
{
  "app_name": "Test MCP Server",
  "version": "1.0.0",
  "features": {
    "tools": true,
    "prompts": true,
    "resources": true
  },
  "limits": {
    "max_requests_per_minute": 100,
    "max_concurrent_connections": 10
  }
}
"""

@mcp.resource("docs://getting-started")
def get_getting_started_docs() -> str:
    """Get getting started documentation"""
    return """
# Getting Started with Test MCP Server

## Overview
This is a comprehensive test server for the Model Context Protocol (MCP).

## Available Features

### Tools
- `add_numbers`: Add two numbers
- `get_user_info`: Retrieve user information
- `search_items`: Search for items

### Prompts
- `code_review_prompt`: Generate code review prompts
- `summarize_prompt`: Generate summarization prompts

### Resources
- `config://app`: Application configuration
- `docs://getting-started`: This documentation
- `data://sample`: Sample data

## Usage
Connect to this server using an MCP client and explore the available tools, prompts, and resources.
"""

@mcp.resource("data://sample")
def get_sample_data() -> str:
    """Get sample data"""
    return """
[
  {"id": 1, "name": "Alice", "role": "Developer"},
  {"id": 2, "name": "Bob", "role": "Designer"},
  {"id": 3, "name": "Charlie", "role": "Manager"}
]
"""

# ============================================================================
# DYNAMIC RESOURCES - Resources that can be listed
# ============================================================================

# You can also create dynamic resources that respond to patterns
# For example, user profiles:
# @mcp.resource("user://{user_id}")
# def get_user_profile(user_id: str) -> str:
#     return f"Profile for user {user_id}"

if __name__ == "__main__":
    # Run the server
    mcp.run()
