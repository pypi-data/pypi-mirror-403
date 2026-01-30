"""
Compute Module

Provides an interface to query ClickHouse databases | Minio storage | Opensearch indices from Atlas notebooks.
"""

import os
import pandas as pd
from clickhouse_driver import Client
from minio import Minio
from opensearchpy import OpenSearch
from .repositories.requests_repo import RequestsRepo

class ComputeClient:
    """Client for executing queries against ClickHouse | Minio | Opensearch."""
    
    def __init__(self, username = Optional[str], password = Optional[str], warehouse_id, token = Optional[str] = None):
        """Authenticates the current user"""

        self.warehouse_id = warehouse_id
        self.token = token
        if token:   
            self.requests_repo = RequestsRepo(
                base_url="https://atlas-orchestrator.atlas.coreoutline.com",
                token=token
            )
        elif username and password:
            self.requests_repo = RequestsRepo(
                base_url="https://atlas-orchestrator.atlas.coreoutline.com",
                username=username,
                password=password
            )
        else:
            raise ValueError("Username and password or token must be provided")

        self.get_credentials()
    
    def get_credentials(self):
        """
        Get credentials for client creation from /warehouses/<warehouse_id>/credentials
        """
        try:
            response = self.requests_repo.get(f"api/admin/warehouses/{self.warehouse_id}/credentials")
            self.credentials = response.json()
            return self.credentials
        except Exception as e:
            raise ConnectionError(f"Failed to get credentials: {str(e)}")


    def create_client(self, client_type: str):
        """Create a client for ClickHouse | Minio | Opensearch."""
        assert client_type in ["sql", "storage", "search"]
        if self.credentials is None:
            raise ConnectionError("Warehouse credentials not found")
        try:
            if client_type == "sql":
                self.client = Client(
                    host=self.credentials["clickhouse"]["host"],
                    port=int(self.credentials["clickhouse"]["port"]),
                    user=self.credentials["clickhouse"]["username"],
                    password=self.credentials["clickhouse"]["password"],
                    database=self.credentials["clickhouse"]["database"],
                    secure=True,
                    verify=False
                )
                return self.client
            elif client_type == "search":
                self.client = OpenSearch(
                    hosts=[{'host': self.credentials["opensearch"]["host"], 'port': int(self.credentials["opensearch"]["port"])}],
                    use_ssl=False,
                    secure=True
                )
                return self.client
            elif client_type == "storage":
                self.client = Minio(
                    endpoint=self.credentials["minio"]["host"]+":"+str(self.credentials["minio"]["port"]),
                    access_key=self.credentials["minio"]["username"],
                    secret_key=self.credentials["minio"]["password"],
                    secure=False  # Use HTTP instead of HTTPS
                ) 
                return self.client
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {client_type}: {str(e)}")
