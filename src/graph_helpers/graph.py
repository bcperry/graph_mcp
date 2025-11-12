from configparser import SectionProxy
from typing import Union
from azure.identity import (
    InteractiveBrowserCredential,
)  # Changed from DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import (
    UserItemRequestBuilder,
)
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)
from azure.identity import OnBehalfOfCredential

import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class Graph:
    settings: SectionProxy
    device_code_credential: Union[
        InteractiveBrowserCredential, OnBehalfOfCredential
    ]  # Changed type
    user_client: GraphServiceClient

    def __init__(
        self, config: SectionProxy, obo_credential: OnBehalfOfCredential = None
    ):
        self.settings = config
        graph_scopes = self.settings["graphUserScopes"].split(" ")

        if obo_credential:
            logger.info(
                f"Initializing Graph client with obo_credential creds. Type: {type(obo_credential)}"
            )
            self.device_code_credential = obo_credential
        else:
            logger.info("Initializing Graph client without token.")
            client_id = self.settings["clientId"]
            tenant_id = self.settings["tenantId"]

            self.device_code_credential = InteractiveBrowserCredential(
                client_id=client_id,
                tenant_id=tenant_id,
                redirect_uri="http://localhost:8000",  # Add redirect URI
            )
        self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)

    async def get_user_token(self):
        logger.info("Getting user token...")
        graph_scopes = self.settings["graphUserScopes"]
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token

    async def get_user(self):
        # Only request specific properties using $select
        query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
            select=["displayName", "mail", "userPrincipalName"]
        )

        request_config = (
            UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
        )

        user = await self.user_client.me.get(request_configuration=request_config)
        return user

    async def get_inbox(self):
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            # Only request specific properties
            select=["from", "isRead", "receivedDateTime", "subject"],
            # Get at most 25 results
            top=25,
            # Sort by received time, newest first
            orderby=["receivedDateTime DESC"],
        )
        request_config = (
            MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
        )

        # NOTE: this method requires Mail.Read permission, which requires admin consent we will be returning dummy data for now

        messages = await self.user_client.me.mail_folders.by_mail_folder_id(
            "inbox"
        ).messages.get(request_configuration=request_config)

        # messages = []  # Dummy data

        return messages
