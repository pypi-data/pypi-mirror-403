# IDSecure Python SDK & CLI

A Python client and CLI tool for interacting with the IDSecure API. This project provides a simple and intuitive interface to manage users, devices, and view logs within your IDSecure instance.

## Installation

Install via pip:

```bash
pip install idsecure-cli
```

Or install from source:

```bash
git clone https://github.com/tsuriu/idsecure-cli.git
cd idsecure-cli
pip install .
```

## CLI Usage

The package includes a command-line interface `idsecure-cli`.

### Configuration

You can provide credentials via flags or environment variables:

- `--url` / `IDSECURE_BASE_URL`
- `--user` / `IDSECURE_USERNAME`
- `--password` / `IDSECURE_PASSWORD`

### Commands

```bash
# List all users
idsecure-cli list-users

# List all devices
idsecure-cli list-devices

# Get details for a specific user
idsecure-cli get-user --id 123

# Delete a user
idsecure-cli delete-user --id 123
```

## SDK Usage

You can also use the `IDSecureClient` directly in your Python scripts.

### Initialization

```python
import asyncio
from idsecure_cli import IDSecureClient

async def main():
    # Initialize the client
    client = IDSecureClient(
        base_url="https://your-idsecure-instance.com", 
        username="your-username", 
        password="your-password"
    )

    # All client methods are asynchronous
    async with client:
        users = await client.list_users()
        print(f"Total users: {users.get('recordsTotal')}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Requirements

- Python 3.8+
- `httpx`
- `click`
- `loguru`

## License

This project is licensed under the MIT License.
