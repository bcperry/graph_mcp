
# Microsoft Graph MCP Server

A FastMCP server that provides authenticated access to Microsoft Graph API, deployable to Azure App Service using Azure Developer CLI (azd).

This MCP server enables AI assistants to interact with Microsoft 365 services on behalf of users through a secure, token-based authentication flow using Azure AD.

## Features

- **Azure AD Authentication**: Secure OAuth2 authentication with On-Behalf-Of (OBO) flow
- **Microsoft Graph Integration**: Access user profiles, emails, and other Microsoft 365 resources
- **FastMCP Framework**: Built on FastMCP for easy MCP server development
- **Azure Deployment Ready**: Includes complete infrastructure-as-code with Bicep templates

## Available Tools

The server exposes the following MCP tools:

- **`get_user_info`**: Returns information about the authenticated Azure user from the access token claims
- **`greet_user`**: Retrieves the user's profile from Microsoft Graph and returns a personalized greeting
- **`display_access_token`**: Returns the user's Graph API access token for direct API calls
- **`list_email_messages`**: Placeholder for email message retrieval (implementation in progress)

## Architecture

The server uses:
- **FastMCP** with Azure authentication provider for OAuth2 flows
- **On-Behalf-Of Flow**: Exchanges the MCP connection token for a Microsoft Graph token
- **Microsoft Graph SDK**: For type-safe Graph API interactions
- **Graph Helper**: Custom wrapper (`src/graph_helpers/graph.py`) for Graph client management

### Authentication Flow

1. Client authenticates with Azure AD and gets an access token
2. Client connects to MCP server with the access token
3. Server validates token using `AzureProvider`
4. For Graph API calls, server uses OBO flow to exchange token for Graph access token
5. Server makes authenticated Graph API calls on behalf of the user

## Prerequisites

- [Azure Developer CLI (azd)](https://aka.ms/azure-dev/install)
- Python 3.12 or higher
- An Azure subscription
- An Azure AD app registration with appropriate Microsoft Graph permissions

## Required Environment Variables

Create a `.env` file or set the following environment variables:

```bash
AZURE_CLIENT_ID=<your-azure-ad-app-client-id>
AZURE_CLIENT_SECRET=<your-azure-ad-app-client-secret>
AZURE_TENANT_ID=<your-azure-ad-tenant-id>
AZURE_GRAPH_USER_SCOPES="User.Read Mail.Read"  # Space-separated scopes
```

## Azure AD App Configuration

Your Azure AD app registration needs:

1. **API Permissions**:
   - Microsoft Graph > Delegated Permissions > `User.Read`
   - Microsoft Graph > Delegated Permissions > `Mail.Read` (if using email features)

2. **Authentication**:
   - Configure redirect URIs as needed for your deployment
   - Enable "Access tokens" and "ID tokens" in Authentication settings

3. **Expose an API**:
   - Add an Application ID URI (e.g., `api://<client-id>`)
   - Define scopes (e.g., `read`) that match the `required_scopes` in `app.py`

4. **Certificates & secrets**:
   - Create a client secret and store it securely

## Usage

### Local Development

1. Clone the repository
```bash
git clone <your-repo-url>
cd graph_mcp
```

2. Install dependencies
```bash
pip install -e .
```

3. Configure environment variables in `.env`

4. Run the server locally
```bash
python src/app.py
```

The server will start on `http://localhost:8000`

### Deploy to Azure

1. Clone the repo and install AZD

2. Login to your Azure account.
```bash
azd auth login
```
> NOTE: if using a government cloud, you will need to configure azd to use that cloud before logging in
```bash
azd config set cloud.name AzureUSGovernment
azd auth login
```

3. Run the following command to build a deployable copy of your application, provision the template's infrastructure to Azure and also deploy the applciation code to those newly provisioned resources.

```bash
azd up
```
> NOTE: the first run will prompt you ```Enter a unique environment name:``` This will be used as a prefix for the resource group that will be created to hold all Azure resources. This name should be unique within your Azure subscription.

This command will prompt you for the following information:
- `Azure Location`: The Azure location where your resources will be deployed.
- `Azure Subscription`: The Azure Subscription where your resources will be deployed.

> NOTE: This may take a while to complete as it executes three commands: `azd package` (builds a deployable copy of your application), `azd provision` (provisions Azure resources), and `azd deploy` (deploys application code). You will see a progress indicator as it packages, provisions and deploys your application.

4. Then make changes to app.py and run `azd deploy` again to update your changes.

## Project Structure

```
graph_mcp/
├── src/
│   ├── app.py                  # Main FastMCP server with authentication
│   ├── requirements.txt        # Python dependencies
│   └── graph_helpers/
│       └── graph.py           # Microsoft Graph client wrapper
├── infra/
│   ├── main.bicep             # Main Bicep infrastructure template
│   ├── main.parameters.json   # Infrastructure parameters
│   └── resources.bicep        # Azure resources definition
├── azure.yaml                 # Azure Developer CLI configuration
├── pyproject.toml            # Python project configuration
└── README.md
```

## App Service Pricing

The template uses Azure App Service. You can choose different pricing tiers by editing `/infra/resources.bicep`:

- **Free Tier (F1)**: Up to 10 apps, limited CPU/RAM - Change line 58 to `"F1"`
- **Basic Tier (B1)**: Default, suitable for development - `"B1"` (current setting)
- **Developer Tier (D1)**: Discounted rate for more apps - `"D1"`

See the [App Service pricing guide](https://azure.microsoft.com/pricing/details/app-service/windows/#pricing) for details.

## Adding More Tools

To extend the server with additional Microsoft Graph capabilities:

1. Add new tool functions in `src/app.py` using the `@mcp.tool()` decorator
2. Use `get_access_token()` to retrieve the authenticated user's token
3. Call `_get_graph_client(token)` to get an authenticated Graph client
4. Use the Graph SDK methods to interact with Microsoft 365 services

Example:
```python
@mcp.tool()
async def get_calendar_events() -> dict:
    """Get the user's calendar events."""
    token = get_access_token()
    graph = await _get_graph_client(user_token=token)
    # Use graph.user_client.me.calendar.events.get() etc.
    ...
```

## Security Considerations

- Store secrets securely (use Azure Key Vault in production)
- Implement proper scope validation for Graph API access
- Use HTTPS for all production deployments
- Follow the principle of least privilege for Graph API permissions
- Regularly rotate client secrets

## Troubleshooting

**Authentication Errors**: Verify your Azure AD app registration settings and ensure the client ID, secret, and tenant ID are correct.

**Graph API Permission Errors**: Check that your app registration has the required delegated permissions and admin consent if needed.

**OBO Flow Issues**: Ensure the `identifier_uri` in `app.py` matches your Azure AD app's Application ID URI.

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Microsoft Graph Documentation](https://learn.microsoft.com/graph/)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

## License

See [LICENSE](LICENSE) file for details.
