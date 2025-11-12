import os
from fastmcp import FastMCP
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph_helpers.graph import Graph
from fastmcp.server.dependencies import get_access_token
from azure.identity import OnBehalfOfCredential
from fastmcp.server.auth.providers.azure import AzureProvider

from dotenv import load_dotenv

load_dotenv()


client_id = os.environ.get("AZURE_CLIENT_ID")
client_secret = os.environ.get("AZURE_CLIENT_SECRET")
tenant_id = os.environ.get("AZURE_TENANT_ID")
user_scopes = os.environ.get("AZURE_GRAPH_USER_SCOPES", "User.Read").split(" ")


# The AzureProvider handles Azure's token format and validation
auth_provider = AzureProvider(
    client_id=client_id,
    client_secret=client_secret,  # Your Azure App Client Secret
    tenant_id=tenant_id,  # Your Azure Tenant ID (REQUIRED)
    # base_url="http://localhost:3978/tools",      # Must include the mount path where MCP is mounted
    base_url="http://localhost:8000",  # Must include the mount path where MCP is mounted
    required_scopes=[
        "read"
    ],  # At least one scope REQUIRED - name of scope from your App
    identifier_uri=f"api://{client_id}",  # Use the actual client_id from environment
    # Optional: request additional upstream scopes in the authorize request
    # additional_authorize_scopes=["User.Read", "offline_access", "openid", "email"],
    # redirect_path="/auth/callback"              # Default value, customize if needed
)

# Initialize FastMCP server
mcp = FastMCP("graph", auth=auth_provider)


async def _get_graph_client(user_token: str) -> Graph:
    """
    Create and return an authenticated Microsoft Graph client.

    If user_token is provided, uses On-Behalf-Of flow to get a Graph token.
    Otherwise, uses client credentials flow for app-only access.

    Requires environment variables:
    - MicrosoftAppId (or AZURE_CLIENT_ID)
    - MicrosoftAppPassword (or AZURE_CLIENT_SECRET)
    - MicrosoftAppTenantId (or AZURE_TENANT_ID)
    """

    if not all([client_id, client_secret, tenant_id]):
        raise ValueError(
            "Missing required environment variables for Microsoft Graph authentication. "
            "Required: MicrosoftAppId, MicrosoftAppPassword, MicrosoftAppTenantId"
        )

    # Create settings
    azure_settings = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "tenantId": tenant_id,
        "graphUserScopes": " ".join(user_scopes),
    }

    # If we have a user token, exchange it for a Graph token using OBO flow

    # Extract just the token string if it's a token object
    token_string = user_token.token if hasattr(user_token, "token") else user_token

    obo_credential = OnBehalfOfCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        user_assertion=token_string,
    )

    # Get a token for Microsoft Graph
    # graph_token = obo_credential.get_token("https://graph.microsoft.com/.default")

    graph = Graph(azure_settings, obo_credential=obo_credential)
    return graph


# Add a protected tool to test authentication
@mcp.tool
async def get_user_info() -> dict:
    """Returns information about the authenticated Azure user based on the MCP server connection access token."""

    token = get_access_token()
    # The AzureProvider stores user data in token claims
    return {
        "azure_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name"),
        "job_title": token.claims.get("job_title"),
        "office_location": token.claims.get("office_location"),
    }


@mcp.tool()
async def greet_user() -> dict:
    """
    Greet a user by retrieving their information from Microsoft Graph.

    This tool retrieves the authenticated user's profile information and returns
    a greeting with their display name and email.

    Returns:
        dict: A dictionary containing:
            - greeting (str): The greeting message
            - display_name (str): User's display name
            - email (str): User's email address (mail or userPrincipalName)
            - success (bool): Whether the operation was successful
            - error (str, optional): Error message if something went wrong

    """
    try:
        # Get authenticated Graph client
        token = get_access_token()
        graph = await _get_graph_client(user_token=token)

        # Get user information using the Graph helper
        user = await graph.get_user()

        if user:
            display_name = user.display_name or "User"
            # For Work/school accounts, email is in mail property
            # Personal accounts, email is in userPrincipalName
            email = user.mail or user.user_principal_name or "No email found"

            greeting = f"Hello, {display_name}!"

            return {
                "greeting": greeting,
                "display_name": display_name,
                "email": email,
                "success": True,
            }
        else:
            return {
                "greeting": "Hello!",
                "error": "Unable to retrieve user information",
                "success": False,
            }

    except ODataError as odata_error:
        error_msg = "Unknown error"
        if odata_error.error:
            error_msg = f"{odata_error.error.code}: {odata_error.error.message}"

        return {"greeting": "Hello!", "error": error_msg, "success": False}
    except Exception as e:
        return {"greeting": "Hello!", "error": str(e), "success": False}


@mcp.tool()
async def display_access_token() -> dict:
    """
    Retrieve and display the user's access token from Microsoft Graph.

    This tool gets the access token for the authenticated user which can be used
    to make direct Graph API calls.

    Returns:
        dict: A dictionary containing:
            - token (str): The user's access token
            - success (bool): Whether the operation was successful
            - error (str, optional): Error message if something went wrong

    Note: Access tokens are sensitive and should be handled securely.
    """
    try:
        # Get authenticated Graph client
        token = get_access_token()
        graph = await _get_graph_client(user_token=token)

        # Get user token using the Graph helper
        token = await graph.get_user_token()

        if token:
            return {"token": token, "success": True}
        else:
            return {"error": "Unable to retrieve access token", "success": False}

    except Exception as e:
        return {"error": str(e), "success": False}


@mcp.tool()
async def list_email_messages(params: dict) -> dict:
    """
    Placeholder implementation for fetching graph data.

    Args:
        params: Dictionary containing request parameters
            - user_id (str, optional): User ID to fetch data for

    Returns:
        dict: Simulated graph data
    """
    user_id = params.get("user_id", "default_user")
    # Simulate fetching data from Microsoft Graph
    graph_data = {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
    }
    return graph_data


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
