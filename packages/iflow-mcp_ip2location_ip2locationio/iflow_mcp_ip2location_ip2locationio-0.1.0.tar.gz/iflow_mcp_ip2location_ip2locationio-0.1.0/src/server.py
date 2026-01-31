from typing import Any, Dict
import httpx
from mcp.server.fastmcp import FastMCP
import os

# Initialize FastMCP server
mcp = FastMCP("ip2locationio")

# Constants
IPLIO_API_BASE = "https://api.ip2location.io"
USER_AGENT = "ip2locationio-app/1.0"

def get_api_key() -> str | None:
    """Retrieve the API key from MCP server config."""
    return os.getenv("IP2LOCATION_API_KEY")

async def make_request(url: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the IP2Location.io API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_geolocation(ip: str) -> Dict[str, Any] | str:
    """
    Fetch geolocation for the given IP address.

    It helps users to retrieve detailed information such as country, region, city, latitude, longitude, ZIP code, time zone, ASN, and proxy information for any IPv4 or IPv6 address

    Args:
        ip: The IP address to analyze (IPv4 or IPv6).

    Returns:
        A JSON string result includes:

        Location & Geography:
        Country, region, district, city, ZIP code, latitude & longitude, time zone.

        Network & Connectivity
        ASN (Autonomous System Number), ISP (Internet Service Provider), domain, net speed, IDD code, area code, address type, usage type.

        Mobile Information
        MNC (Mobile Network Code), MCC (Mobile Country Code), Mobile Brand.

        Currency & Language
        currency code, currency name, currency symbol, language code, language name.

        Proxy & Security
        proxy type, last seen, threat level/type, proxy provider, fraud score.

        Others
        IAB category, weather, elevation, population and more.

        Note that some information may only available in paid plan. Learn more on this in https://www.ip2location.io/pricing.
    """
    params = {"ip": ip}
    api_key = get_api_key()
    if api_key:
        params["key"] = api_key  # IP2Location.io API key parameter

    geolocation_result = await make_request(IPLIO_API_BASE, params)

    if not geolocation_result:
        return f"Unable to fetch geolocation for IP {ip}."

    return geolocation_result

if __name__ == "__main__":
    mcp.run(transport='stdio')

def main():
    """Entry point for the server when installed as a package."""
    mcp.run(transport='stdio')