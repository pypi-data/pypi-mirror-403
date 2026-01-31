from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import os
from dice_roller import DiceRoller

load_dotenv()

mcp = FastMCP("websearch-server")
tavily_api_key = os.getenv("TAVILY_API_KEY")
client = TavilyClient(tavily_api_key) if tavily_api_key else None

@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for information about the given query"""
    if client:
        search_results = client.get_search_context(query=query)
        return search_results
    else:
        return f"[DEMO MODE] Simulated search results for: {query}. Please configure TAVILY_API_KEY to get real search results."

@mcp.tool()
def roll_dice(notation: str, num_rolls: int = 1) -> str:
    """Roll the dice with the given notation"""
    roller = DiceRoller(notation, num_rolls)
    return str(roller)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()