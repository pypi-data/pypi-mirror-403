# Auth related imports
import os
from urllib.parse import urlparse
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response, HTMLResponse
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.auth.middleware.auth_context import get_access_token

# Import auth utilities only if not in test mode
if not os.getenv("TEST_MODE"):
    from auth.auth_utilities import ConsentCookieReader, HashSignatureUtility, Scope
    from auth.consent_dialog import ConsentDialog
    from auth.entraid_auth_settings import EntraIdAuthSettings
    from auth.entraid_oauth_provider import EntraIDOAuthProvider

# end auth related imports

from fastmcp import FastMCP
import logging

from tools.azure_user_info_utility import EntraUserInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Check if running in test mode
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if not TEST_MODE:
    auth_settings = EntraIdAuthSettings()
    target_scope = Scope("user.read")
    hashing_util = HashSignatureUtility(auth_settings.auth_hash_key)
    entra_auth = EntraIDOAuthProvider(
        tenant_id=auth_settings.auth_tenant_id,
        client_id=auth_settings.auth_client_id,
        redirect_uri=auth_settings.auth_redirect_uri,
        scope=target_scope,
    )

    mcp = FastMCP(
        "azure_user_mcp_server",
        auth_server_provider=entra_auth,
        auth=AuthSettings(
            issuer_url="http://localhost:8000",
            client_registration_options=ClientRegistrationOptions(enabled=True),
        ),
    )
else:
    # Test mode - no authentication
    mcp = FastMCP("azure_user_mcp_server")


@mcp.tool()
def get_user_name() -> str:
    """this is a tool to get my user name from the Entra ID."""
    if TEST_MODE:
        return "Test User (Mock mode)"

    try:
        # Get the access token from the MCP server for current authenticated user
        mcp_server_access_token = get_access_token()
        # Use the Entra ID OAuth provider to get the Entra ID access token
        entra_id_access_token = entra_auth.get_entra_id_token(mcp_server_access_token.token)
        if not entra_id_access_token:
            raise Exception("Failed to get Entra ID access token")

        userInfo = EntraUserInfo(bearer_token=entra_id_access_token.access_token)
        user_name = userInfo.get_user_name()
        if user_name:
            return f"User name is {user_name}"
        else:
            return "User name not found"
    except Exception as e:
        logger.error(f"Error getting user name: {e}")
        return "Error getting user name"


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    if TEST_MODE:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse")


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MCP server...")
    if TEST_MODE:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse")