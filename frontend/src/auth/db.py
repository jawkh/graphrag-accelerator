# Copyright Jonathan AW.
# Licensed under the MIT License.

from azure.cosmos import (
    ContainerProxy,
    CosmosClient,
    DatabaseProxy,
)
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential
from environs import Env

from .models import User

ENDPOINT_ERROR_MSG = "Could not find COSMOS_URI_ENDPOINT in environment variables"

from dotenv import load_dotenv

load_dotenv()


class CosmosClientSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            endpoint = Env().str("COSMOS_URI_ENDPOINT", ENDPOINT_ERROR_MSG)
            credential = DefaultAzureCredential()
            cls._instance = CosmosClient(endpoint, credential)
        return cls._instance


def get_database_client(database_name: str) -> DatabaseProxy:
    client = CosmosClientSingleton.get_instance()
    return client.get_database_client(database_name)


def get_database_container_client(
    database_name: str, container_name: str
) -> ContainerProxy:
    db_client = get_database_client(database_name)
    return db_client.get_container_client(container_name)


class AzureStorageClientManager:
    """
    Manages the Azure storage clients for Cosmos DB.

    Attributes:
        cosmos_uri_endpoint (str): The uri endpoint for the Cosmos DB.
        _cosmos_client (CosmosClient): The Cosmos DB client.
        _cosmos_database_client (DatabaseProxy): The Cosmos DB database client.
        _cosmos_container_client (ContainerProxy): The Cosmos DB container client.
    """

    def __init__(self) -> None:
        self._env = Env()
        # self.cosmos_uri_endpoint = self._env.str(
        #     "COSMOS_URI_ENDPOINT", ENDPOINT_ERROR_MSG
        # )
        self.cosmos_uri_endpoint = (
            "https://cosmos-24eoykjjvgrfi.documents.azure.com:443/"
        )
        credential = DefaultAzureCredential()
        self._cosmos_client = CosmosClient(
            url=self.cosmos_uri_endpoint, credential=credential
        )

    def get_cosmos_client(self) -> CosmosClient:
        """
        Returns the Cosmos DB client.

        Returns:
            CosmosClient: The Cosmos DB client.
        """
        return self._cosmos_client

    def get_cosmos_database_client(self, database_name: str) -> DatabaseProxy:
        """
        Returns the Cosmos DB database client.

        Args:
            database_name (str): The name of the database.

        Returns:
            DatabaseProxy: The Cosmos DB database client.
        """
        if not hasattr(self, "_cosmos_database_client"):
            self._cosmos_database_client = self._cosmos_client.get_database_client(
                database=database_name
            )
        return self._cosmos_database_client

    def get_cosmos_container_client(
        self, database_name: str, container_name: str
    ) -> ContainerProxy:
        """
        Returns the Cosmos DB container client.

        Args:
            database_name (str): The name of the database.
            container_name (str): The name of the container.

        Returns:
            ContainerProxy: The Cosmos DB container client.
        """
        if not hasattr(self, "_cosmos_container_client"):
            self._cosmos_container_client = self.get_cosmos_database_client(
                database_name=database_name
            ).get_container_client(container=container_name)
        return self._cosmos_container_client


user_container = AzureStorageClientManager().get_cosmos_container_client(
    Env().str(
        "COSMOS_DB_NAME", "Could not find COSMOS_DB_NAME in environment variables"
    ),
    "user-accounts",
)

graphrag_container_store = AzureStorageClientManager().get_cosmos_container_client(
    Env().str(
        "COSMOS_DB_NAME", "Could not find COSMOS_DB_NAME in environment variables"
    ),
    "container-store",
)


def get_user(username: str) -> User:
    try:
        user_item = user_container.read_item(item=username, partition_key=username)
        return User(**user_item)
    except CosmosResourceNotFoundError:
        return None


def save_user(user: User):
    user_container.upsert_item(user.model_dump())


def list_users():
    query = "SELECT * FROM c"
    users = list(
        user_container.query_items(query=query, enable_cross_partition_query=True)
    )
    return users


def delete_user(username: str) -> bool:
    try:
        user_container.delete_item(item=username, partition_key=username)
        return True
    except CosmosResourceNotFoundError:
        return False


def deactivate_user(username: str) -> bool:
    user = get_user(username)
    if user:
        user.accountstatus = "Inactive"
        save_user(user)
        return True
    return False


def activate_user(username: str) -> bool:
    user = get_user(username)
    if user:
        user.accountstatus = "Active"
        save_user(user)
        return True
    return False


def list_graphrag_indexes():
    """
    Returns the list of available "graphRag indexes" for assigning to the users
    """
    query = "SELECT c.human_readable_name FROM c WHERE c.type = 'index'"
    items = list(
        graphrag_container_store.query_items(
            query=query, enable_cross_partition_query=True
        )
    )
    return [item["human_readable_name"] for item in items]
