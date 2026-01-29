# timeback-core

Unified Python client for all Timeback education APIs.

## Installation

```bash
# pip
pip install timeback-core

# uv (add to a project)
uv add timeback-core

# uv (install into current environment)
uv pip install timeback-core
```

## Quick Start

```python
from timeback_core import TimebackClient

async def main():
    client = TimebackClient(
        env="staging",  # or "production"
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

    # OneRoster - rostering and gradebook
    users = await client.oneroster.users.list()
    for user in users:
        print(f"{user.given_name} {user.family_name}")

    # Edubridge - simplified enrollments and analytics
    analytics = await client.edubridge.analytics.summary()

    # Caliper - learning analytics events
    await client.caliper.events.send(sensor_id, events)

    await client.close()
```

## Managing Multiple Clients

For applications that need to manage multiple `TimebackClient` instances, use `TimebackManager`:

```python
from timeback_core import TimebackManager

async def main():
    manager = TimebackManager()
    manager.register("alpha", env="production", client_id="...", client_secret="...")
    manager.register("beta", env="production", client_id="...", client_secret="...")

    # Target a specific platform
    users = await manager.get("alpha").oneroster.users.list()

    # Broadcast to all platforms (uses asyncio.gather — never raises)
    async def create_user(client):
        return await client.oneroster.users.create(user_data)

    results = await manager.broadcast(create_user)

    # Check results
    if results.all_succeeded:
        print("Synced to all platforms!")

    for name, user in results.succeeded:
        print(f"Created on {name}: {user}")

    for name, error in results.failed:
        print(f"Failed on {name}: {error}")

    await manager.close()
```

### Manager API

| Method                   | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `register(name, **cfg)`  | Add a named client                               |
| `get(name)`              | Retrieve a client by name                        |
| `has(name)`              | Check if a client is registered                  |
| `names`                  | Get all registered client names                  |
| `size`                   | Get number of registered clients                 |
| `broadcast(fn)`          | Execute on all clients, returns `BroadcastResults` |
| `unregister(name)`       | Remove a client                                  |
| `close()`                | Close all clients                                |

### BroadcastResults API

| Property/Method | Description                                 |
| --------------- | ------------------------------------------- |
| `succeeded`     | Get successful results as `[(name, value)]` |
| `failed`        | Get failed results as `[(name, error)]`     |
| `all_succeeded` | `True` if all operations succeeded          |
| `any_failed`    | `True` if any operation failed              |
| `values()`      | Get all values (raises if any failed)       |

## Configuration

The client supports three configuration modes:

### Environment Mode (Recommended)

Derive all URLs from `staging` or `production`:

```python
client = TimebackClient(
    env="staging",  # or "production"
    client_id="...",
    client_secret="...",
)
```

| Environment  | API Base URL                   |
| ------------ | ------------------------------ |
| `staging`    | `api.staging.alpha-1edtech.ai` |
| `production` | `api.alpha-1edtech.ai`         |

### Base URL Mode

For self-hosted or custom deployments with a single base URL:

```python
client = TimebackClient(
    base_url="https://timeback.myschool.edu",
    auth_url="https://timeback.myschool.edu/oauth/token",
    client_id="...",
    client_secret="...",
)
```

### Explicit Services Mode

Full control over each service URL:

```python
client = TimebackClient(
    services={
        "oneroster": "https://roster.example.com",
        "caliper": "https://analytics.example.com",
        "edubridge": "https://api.example.com",
    },
    auth_url="https://auth.example.com/oauth/token",
    client_id="...",
    client_secret="...",
)
```

## Individual Clients

For standalone usage, install individual packages:

```bash
pip install timeback-oneroster
pip install timeback-edubridge
pip install timeback-caliper
```

```python
from timeback_oneroster import OneRosterClient

client = OneRosterClient(
    env="staging",
    client_id="...",
    client_secret="...",
)
```

## Environment Variables

If credentials are not provided explicitly, the client reads from:

- `TIMEBACK_ENV` - Environment (staging/production)
- `TIMEBACK_CLIENT_ID`
- `TIMEBACK_CLIENT_SECRET`
- `TIMEBACK_TOKEN_URL` (optional)

## Async Context Manager

```python
async with TimebackClient(env="staging", client_id="...", client_secret="...") as client:
    schools = await client.oneroster.schools.list()
# Client is automatically closed
```

## Error Handling

```python
from timeback_core import OneRosterError, CaliperError, EdubridgeError

try:
    users = await client.oneroster.users.list()
except OneRosterError as e:
    print(f"OneRoster API error: {e}")
except CaliperError as e:
    print(f"Caliper API error: {e}")
except EdubridgeError as e:
    print(f"Edubridge API error: {e}")
```
