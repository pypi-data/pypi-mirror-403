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
from typing import Optional

class ComputeClient:
    """Client for executing queries against ClickHouse | Minio | Opensearch."""
    
    def __init__(
        self, 
        warehouse_id: str, 
        username: Optional[str] = None, 
        password: Optional[str] = None, 
        token: Optional[str] = None,
        base_url: str = "https://atlas-orchestrator.atlas.coreoutline.com"
    ):
        """
        Initializes the ComputeClient.
        
        Args:
            warehouse_id: The ID of the warehouse to connect to.
            username: Optional username for authentication.
            password: Optional password for authentication.
            token: Optional direct token for authentication.
            base_url: Base URL of the Atlas Orchestrator.
        """
        self.warehouse_id = warehouse_id
        self.token = token
        self.credentials = None
        
        if token:   
            self.requests_repo = RequestsRepo(base_url=base_url, token=token)
        elif username and password:
            self.requests_repo = RequestsRepo(base_url=base_url, username=username, password=password)
        else:
            raise ValueError("Either a token or both username and password must be provided for authentication.")

        self.get_credentials()
    
    def get_credentials(self):
        """
        Fetches credentials for the warehouse from the orchestrator.
        """
        try:
            response = self.requests_repo.get(f"api/admin/warehouses/{self.warehouse_id}/credentials")
            self.credentials = response.json()
            return self.credentials
        except Exception as e:
            raise ConnectionError(f"Failed to fetch warehouse credentials: {str(e)}")

    def create_client(self, client_type: str):
        """
        Creates a client for the specified service.
        
        Args:
            client_type: One of "sql" (ClickHouse), "storage" (Minio), or "search" (OpenSearch).
        """
        valid_types = ["sql", "storage", "search"]
        if client_type not in valid_types:
            raise ValueError(f"Invalid client_type. Must be one of {valid_types}")
            
        if not self.credentials:
            raise ConnectionError("Warehouse credentials not available. Call get_credentials() first.")
            
        try:
            if client_type == "sql":
                ch_config = self.credentials.get("clickhouse", {})
                return Client(
                    host=ch_config["host"],
                    port=int(ch_config["port"]),
                    user=ch_config["username"],
                    password=ch_config["password"],
                    database=ch_config["database"],
                    secure=True,
                    verify=False
                )
            elif client_type == "search":
                os_config = self.credentials.get("opensearch", {})
                return OpenSearch(
                    hosts=[{'host': os_config["host"], 'port': int(os_config["port"])}],
                    use_ssl=False,
                    secure=True,
                    http_auth=(os_config.get("username"), os_config.get("password")) if "username" in os_config else None
                )
            elif client_type == "storage":
                minio_config = self.credentials.get("minio", {})
                endpoint = f"{minio_config['host']}:{minio_config['port']}"
                return Minio(
                    endpoint=endpoint,
                    access_key=minio_config["username"],
                    secret_key=minio_config["password"],
                    secure=False,
                )
        except KeyError as e:
            raise ConnectionError(f"Missing required credential field for {client_type}: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize {client_type} client: {str(e)}")
