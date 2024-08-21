# Copyright Jonathan AW.
# Licensed under the MIT License.

import json

from azure.cosmos import (
    ContainerProxy,
    CosmosClient,
    DatabaseProxy,
)
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient
from environs import Env

from .models import User

# Error messages
ENDPOINT_ERROR_MSG = "Could not find COSMOS_URI_ENDPOINT in environment variables"
ENDPOINT_ERROR_MSG_AZUREBLOB = (
    "Could not find AZUREBLOB_URI_ENDPOINT in environment variables"
)

from dotenv import load_dotenv

load_dotenv()


class BlobServiceClientSingleton:
    _instance = None
    _env = Env()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            account_url = cls._env.str(
                "STORAGE_ACCOUNT_BLOB_URL", ENDPOINT_ERROR_MSG_AZUREBLOB
            )
            credential = DefaultAzureCredential()
            cls._instance = BlobServiceClient(account_url, credential=credential)
        return cls._instance

    @classmethod
    def get_storage_account_name(cls):
        account_url = cls._env.str(
            "STORAGE_ACCOUNT_BLOB_URL", ENDPOINT_ERROR_MSG_AZUREBLOB
        )
        return account_url.split("//")[1].split(".")[0]


class CosmosClientSingleton:
    _instance = None
    _env = Env()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            endpoint = cls._env.str("COSMOS_URI_ENDPOINT", ENDPOINT_ERROR_MSG)
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
    Manages the Azure storage clients for blob storage and Cosmos DB.

    Attributes:
        azure_storage_blob_url (str): The blob endpoint for azure storage.
        cosmos_uri_endpoint (str): The uri endpoint for the Cosmos DB.
        _blob_service_client (BlobServiceClient): The blob service client.
        _cosmos_client (CosmosClient): The Cosmos DB client.
        _cosmos_database_client (DatabaseProxy): The Cosmos DB database client.
        _cosmos_container_client (ContainerProxy): The Cosmos DB container client.
    """

    def __init__(self) -> None:
        self._env = Env()
        self.azure_storage_blob_url = self._env.str(
            "STORAGE_ACCOUNT_BLOB_URL", ENDPOINT_ERROR_MSG_AZUREBLOB
        )
        self.cosmos_uri_endpoint = self._env.str(
            "COSMOS_URI_ENDPOINT", ENDPOINT_ERROR_MSG
        )
        credential = DefaultAzureCredential()
        self._blob_service_client = BlobServiceClient(
            account_url=self.azure_storage_blob_url, credential=credential
        )
        self._cosmos_client = CosmosClient(
            url=self.cosmos_uri_endpoint, credential=credential
        )

    def get_blob_service_client(self) -> BlobServiceClient:
        """
        Returns the blob service client.

        Returns:
            BlobServiceClient: The blob service client.
        """
        return self._blob_service_client

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


def save_query_histories(blob_name: str, query_histories: list):
    """
    Saves the query histories to Azure Blob Storage.

    Args:
        blob_name (str): The name of the blob file.
        query_histories (list): The query histories data.
    """
    blob_service_client = BlobServiceClientSingleton.get_instance()
    blob_client = blob_service_client.get_blob_client(
        container="query-history", blob=blob_name
    )
    blob_client.upload_blob(json.dumps(query_histories), overwrite=True)


# Function to handle large data saving
def save_large_query_histories(
    blob_client: BlobClient, query_histories: list, max_blob_size=4 * 1024 * 1024
):
    """
    Splits and saves large query histories data to multiple blobs if it exceeds the size limit.

    Args:
        blob_client (BlobClient): The blob client to save the data.
        query_histories (list): The query histories data to be saved.
        max_blob_size (int): The maximum size of each blob in bytes.
    """
    chunk_index = 0
    while query_histories:
        chunk = []
        current_size = 0
        while (
            query_histories
            and current_size + len(json.dumps(query_histories[0])) <= max_blob_size
        ):
            item = query_histories.pop(0)
            chunk.append(item)
            current_size += len(json.dumps(item))

        chunk_blob_name = f"{blob_client.blob_name}_chunk_{chunk_index}"
        chunk_blob_client = blob_client.get_blob_client(chunk_blob_name)
        chunk_blob_client.upload_blob(json.dumps(chunk), overwrite=True)
        chunk_index += 1


def load_query_histories(blob_name: str) -> list:
    """
    Loads the query histories from Azure Blob Storage.

    Args:
        blob_name (str): The name of the blob file.

    Returns:
        list: The query histories data.
    """
    blob_service_client = BlobServiceClientSingleton.get_instance()
    blob_client = blob_service_client.get_blob_client(
        container="query-history", blob=blob_name
    )

    try:
        download_stream = blob_client.download_blob()
        query_context = json.loads(download_stream.readall())
        return query_context
    except Exception as e:
        print(f"Error loading query histories: {e}")
        return []


def list_user_session_names_with_prefix(container_name: str, prefix: str):
    """
    List blobs with a specific prefix synchronously.

    Args:
        container_name (str): The name of the container.
        prefix (str): The prefix to filter blobs by. Eg. "userName__".

    Returns:
        list: A list of User Session Names.
    """
    blob_service_client = BlobServiceClientSingleton.get_instance()
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = []

    for blob in container_client.list_blobs(name_starts_with=prefix):
        blob_list.append(blob.name)

    return blob_list
