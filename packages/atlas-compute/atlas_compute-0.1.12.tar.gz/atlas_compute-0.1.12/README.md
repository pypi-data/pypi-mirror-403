# Atlas Compute

Atlas Compute is a Python SDK for interacting with the Atlas platform's compute resources, including ClickHouse, MinIO, and OpenSearch.

## Installation

```bash
pip install atlas-compute
```

## Usage

### Connecting to Resources

```python
from atlas_compute.compute import ComputeClient

# Initialize the client
computeclient = ComputeClient(
    username="your_username",
    password="your_password",
    warehouse_id="your_warehouse_id"
)

# Get credentials
creds = computeclient.get_credentials()

# Create a data warehouse client
client = computeclient.create_client("warehouse")
result = client.execute("SELECT 1")
print(result)

# Create a storage client
client = computeclient.create_client("storage")
buckets = client.list_buckets()
print(buckets)

# Create a search and analytics client
client = computeclient.create_client("search_and_analytics")
buckets = client.search()
print(buckets)
```

## Features

- **Unified Authentication**: Authenticate once and access all resources.
- **Resource Clients**: Easy creation of clients for data warehouse, storage, and search & analytics.
- **Secure**: Handles credential retrieval and management securely.
