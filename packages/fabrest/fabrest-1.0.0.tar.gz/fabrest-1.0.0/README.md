# FabRest

FabRest is a Python SDK for Microsoft Fabric REST APIs. It provides a consistent, typed surface for managing workspaces and Fabric items with sync and async clients.

## Features

- Authentication via `azure.identity` plus ROPC fallback
- Workspace and item management (create, update, delete, list)
- Data operations for pipelines, notebooks, and more
- Broad API coverage across Fabric resources
- Async support for concurrent workloads

## Installation

```bash
pip install fabrest
```

From source:

```bash
git clone https://github.com/billybillysss/fabrest.git
cd fabrest
pip install .
```

## Quick start

FabRest exposes `FabricClient` and `AsyncFabricClient`. Workspace-scoped resources are accessed via `client.workspace("id")`.

### Authentication

```python
from azure.identity import DefaultAzureCredential
from fabrest import FabricClient

credential = DefaultAzureCredential()
client = FabricClient(credential)
```

```python
from fabrest.api.auth import ResourceOwnerPasswordCredential
from fabrest import FabricClient

credential = ResourceOwnerPasswordCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    username="your-username",
    password="your-password",
)
client = FabricClient(credential)
```

### Core patterns

```python
workspace = client.workspace("workspace-id")

# Workspaces
workspaces = client.workspaces.list()
ws = client.workspaces.get("workspace-id")

# Items (generic)
items = workspace.items.list()
lakehouses = workspace.items_for("Lakehouse").list()
```

## Resource examples

### Item resources and actions

```python
# Lakehouse tables
tables = workspace.lakehouses.list_tables("lakehouse-id")

# SQL endpoint connection string
conn = workspace.sql_endpoints.get_connection_string("sql-endpoint-id")

# Warehouse restore points
restore_points = workspace.warehouses.list_restore_points("warehouse-id")
```

### Data pipeline and notebook actions

```python
# Data pipeline
pipeline_run = workspace.data_pipelines.run("pipeline-id")

# Notebook
notebook_run = workspace.notebooks.run("notebook-id")
```

### Payload interfaces (simple and advanced)

```python
from fabrest.models import dataflow

# Simple payload using a TypedDict interface
payload: dataflow.ExecuteQueryRequest = {
    "queryName": "GetCustomers",
}

result = workspace.dataflows.execute_query("dataflow-id", payload)
```

```python
from fabrest.models import dataflow

# Payload with definition parts
payload: dataflow.CreateDataflowRequest = {
    "displayName": "Customer Dataflow",
    "definition": {
        "parts": [
            {
                "path": "model.json",
                "payloadType": "InlineBase64",
                "payload": "eyJ2ZXJzaW9uIjogIjEiLCAiZW50aXRpZXMiOiBbXX0=",
            }
        ]
    },
}

dataflow_item = workspace.dataflows.create(payload)
```

```python
from fabrest.models import warehouse

# Advanced payload with nested TypedDicts and lists
payload: warehouse.CreateRestorePointRequest = {
    "displayName": "Before schema change",
    "description": "Restore point before ETL migration",
    "retentionDays": 14,
}

restore_point = workspace.warehouses.create_restore_point("warehouse-id", payload)
```

## Async usage

```python
import asyncio
from azure.identity import DefaultAzureCredential
from fabrest import AsyncFabricClient

async def main():
    client = AsyncFabricClient(DefaultAzureCredential())
    workspace = client.workspace("workspace-id")
    reports = await workspace.reports.async_list()
    await client.close()

asyncio.run(main())
```

```python
import asyncio
from azure.identity import DefaultAzureCredential
from fabrest import AsyncFabricClient

async def main():
    client = AsyncFabricClient(DefaultAzureCredential())
    workspace = client.workspace("workspace-id")

    pipeline_run = await workspace.data_pipelines.async_run("pipeline-id")
    notebook_run = await workspace.notebooks.async_run("notebook-id")

    await client.close()

asyncio.run(main())
```

```python
import asyncio
from azure.identity import DefaultAzureCredential
from fabrest import AsyncFabricClient
from fabrest.models import dataflow, warehouse

async def main():
    client = AsyncFabricClient(DefaultAzureCredential())
    workspace = client.workspace("workspace-id")

    simple_payload: dataflow.ExecuteQueryRequest = {"queryName": "GetCustomers"}
    await workspace.dataflows.async_execute_query("dataflow-id", simple_payload)

    advanced_payload: warehouse.CreateRestorePointRequest = {
        "displayName": "Before schema change",
        "description": "Restore point before ETL migration",
        "retentionDays": 14,
    }
    await workspace.warehouses.async_create_restore_point("warehouse-id", advanced_payload)

    await client.close()

asyncio.run(main())
```

## Pagination

```python
page = workspace.lakehouses.list(recursive=True)
next_page = workspace.lakehouses.list(continuation_token="token")
```

List endpoints return aggregated items. The SDK normalizes item lists from both `value` and `data` fields in API responses.

## LRO and raw responses

```python
from fabrest.transport import RequestOptions

options = RequestOptions(wait_for_completion=False, raw_response=True)
response = workspace.lakehouses.create({"displayName": "My Lakehouse"}, options=options)
```

## Error handling

```python
from fabrest.errors import HttpError, ThrottledError

try:
    workspace.sql_endpoints.refresh_metadata("sql-endpoint-id")
except ThrottledError as exc:
    print(exc.status_code, exc.payload)
except HttpError as exc:
    print(exc.status_code, exc.payload)
```

## Documentation

Detailed documentation is under development. For now, refer to the source code and inline comments for usage of modules and functions.

## Contributing

Contributions are welcome. Please open an Issue or submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For support, open an issue on the GitHub repository or contact the maintainers directly.

---

Note: This project is not officially affiliated with Microsoft or the Fabric team.
