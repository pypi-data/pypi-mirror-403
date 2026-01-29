# Redenv Python SDK

The official, zero-knowledge Python client for [Redenv](https://github.com/redenv-labs/redenv). Securely fetch, cache, and manage your environment variables at runtime.

![PyPI - Version](https://img.shields.io/pypi/v/redenv)
![PyPI - License](https://img.shields.io/pypi/l/redenv)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/redenv)

## Features

- **🔒 Zero-Knowledge:** End-to-End Encryption. Secrets are decrypted locally using your Project Encryption Key (PEK).
- **⚡ High Performance:** In-memory `LRUCache` with `Stale-While-Revalidate` strategy for zero-latency reads.
- **🔄 Universal:** Native **Async** (`asyncio`) and **Synchronous** clients included.
- **🛠️ Developer Experience:**
  - **Smart Casting:** `secrets.get("PORT", cast=int)`
  - **Scoping:** `secrets.scope("STRIPE_")` for namespaced configs.
  - **Validation:** `secrets.require("API_KEY")` fail-fast checks.
  - **Time Travel:** Fetch historical versions of secrets.
- **🛡️ Secure by Default:** Secrets are masked (`********`) in logs to prevent accidental leaks.

## Installation

```bash
pip install redenv
```

## Quick Start

### Async Client (FastAPI / Modern Apps)

```python
import asyncio
import os
from redenv import Redenv

async def main():
    client = Redenv({
        "project": os.getenv("REDENV_PROJECT"),
        "token_id": os.getenv("REDENV_TOKEN_ID"),
        "token": os.getenv("REDENV_TOKEN_KEY"),
        "upstash": {
            "url": os.getenv("UPSTASH_REDIS_URL"),
            "token": os.getenv("UPSTASH_REDIS_TOKEN")
        }
    })

    # 1. Load Secrets (Populates os.environ by default)
    secrets = await client.load()
    
    # 2. Access Secrets
    print(f"Database URL: {secrets['DATABASE_URL']}")
    
    # 3. Smart Casting
    port = secrets.get("PORT", cast=int)
    debug = secrets.get("DEBUG", cast=bool)

if __name__ == "__main__":
    asyncio.run(main())
```

### Synchronous Client (Flask / Scripts / Legacy)

Perfect for scripts or frameworks where `async/await` is not available at the top level.

```python
from redenv import RedenvSync

client = RedenvSync({ ... }) # Same config as above

# Blocks until secrets are fetched
secrets = client.load()

print(secrets["API_KEY"])
```

## Advanced Usage

### 1. Scoping & Validation
Organize large configurations and ensure critical keys exist.

```python
secrets = await client.load()

# Fail if these keys are missing
secrets.require("STRIPE_KEY", "STRIPE_WEBHOOK")

# Create a subset of keys (e.g., keys starting with "STRIPE_")
# The prefix is automatically stripped.
stripe_config = secrets.scope("STRIPE_")

print(stripe_config["KEY"])     # Maps to STRIPE_KEY
print(stripe_config["WEBHOOK"]) # Maps to STRIPE_WEBHOOK
```

### 2. Time Travel (Version History)
Redenv stores a history of every secret change. You can access older versions for rollbacks or auditing.

```python
# Get the absolute version 5
v5 = await client.get_version("API_KEY", 5)

# Get the previous version (1 version older than latest)
# Mode="index": 0=Latest, 1=Previous, -1=Oldest
prev = await client.get_version("API_KEY", 1, mode="index")

# Get the oldest version ever created
first = await client.get_version("API_KEY", -1)
```

### 3. Writing Secrets
You can update secrets programmatically. This automatically encrypts the value, increments the version, and updates the history.

```python
await client.set("FEATURE_FLAG", "true")
```

### 4. Configuration Options

| Option | Type | Description | Default |
|:---|:---|:---|:---|
| `project` | str | Your Project ID | Required |
| `token_id` | str | Service Token Public ID | Required |
| `token` | str | Service Token Secret Key | Required |
| `upstash` | dict | `{ url: ..., token: ... }` | Required |
| `environment` | str | Target environment (dev, prod) | `development` |
| `log` | str | Log level (`none`, `low`, `high`) | `low` |
| `cache` | dict | `{ ttl: 300, swr: 86400 }` (seconds) | 5min / 24h |
| `env.override` | bool | Overwrite existing `os.environ` keys | `True` |

```python
client = Redenv({
    # ...
    "env": {
        "override": False # Protects local env vars from being overwritten
    }
})
```

## Security

- **Masking:** If you accidentally print the `secrets` object, values are hidden: `Secrets({'API_KEY': '********'})`.
- **Zero-Knowledge:** The server (Upstash) never sees the plaintext. Decryption happens only in your application's memory.

## License

MIT