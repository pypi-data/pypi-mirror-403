from mcp.client.service import Client
from mcp.types.tools import CallToolRequestParams
from mcp.logger import get_logger, configure_logging
import asyncio

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

async def main():
    client=Client.from_config_file('./mcp_servers/config.json')
    session=await client.create_session('exa-mcp')
    # logger.info("Init Result: %s", session.get_initialize_result())
    tools=await session.list_tools()
    logger.info("Tools: %s", tools.model_dump_json(indent=4))
    # sleep(5)
    await client.close_session('exa-mcp')

if __name__ == '__main__':
    asyncio.run(main())
