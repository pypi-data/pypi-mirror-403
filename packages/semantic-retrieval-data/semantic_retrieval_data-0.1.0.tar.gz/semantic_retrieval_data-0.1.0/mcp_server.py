import argparse
import logging

import yaml
import httpx
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
FASTAPI_BASE_URL = "http://106.51.38.120:8001"

# Global username (set from command line)
CONFIGURED_USERNAME: str = ""

# Initialize MCP server
mcp = FastMCP(
    "Semantic Layer Retrieval",
    instructions="Fast semantic search across structured, semi-structured, and unstructured data"
)


@mcp.tool()
def retrieve(query: str) -> str:
    """
    Retrieve relevant semantic context for a query.

    Args:
        query: The search query

    Returns:
        YAML-formatted results with relevance scores
    """
    logger.info(f"Retrieval: user={CONFIGURED_USERNAME}, query={query}")

    try:
        with httpx.Client(timeout=None) as client:
            response = client.post(
                f"{FASTAPI_BASE_URL}/retrieve",
                data={
                    "username": CONFIGURED_USERNAME,
                    "query": query
                }
            )

            if response.status_code == 200:
                return response.text
            else:
                return yaml.dump({
                    'error': f'API error: {response.status_code}',
                    'detail': response.text,
                    'query': query,
                    'results': []
                })

    except httpx.ConnectError:
        return yaml.dump({
            'error': f'Cannot connect to {FASTAPI_BASE_URL}',
            'query': query,
            'results': []
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return yaml.dump({
            'error': str(e),
            'query': query,
            'results': []
        })


def main():
    global CONFIGURED_USERNAME

    parser = argparse.ArgumentParser(description="MCP Semantic Retrieval Server")
    parser.add_argument("username", help="Username")
    args = parser.parse_args()

    CONFIGURED_USERNAME = args.username

    logger.info(f"MCP Server for user: {CONFIGURED_USERNAME}")
    logger.info(f"FastAPI endpoint: {FASTAPI_BASE_URL}")

    mcp.run()


if __name__ == "__main__":
    main()
