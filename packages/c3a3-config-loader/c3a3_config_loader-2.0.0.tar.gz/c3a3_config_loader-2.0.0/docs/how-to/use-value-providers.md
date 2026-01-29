# How to Use Value Providers

Add dynamic value suggestions to command arguments for autocompletion, help, and validation.

---

## Overview

Value providers supply valid values for arguments. They're used for:

- **Autocompletion**: Suggest values as users type
- **Help generation**: Show available options
- **Validation**: Verify user input
- **Error recovery**: "Did you mean?" suggestions

---

## Basic Usage

### Reference a Provider Function

In your spec, reference a Python function:

```yaml
commands:
  - name: deploy
    terminal: true
    arguments:
      - name: region
        type: string
        values_from: myapp.providers.get_regions
```

### Implement the Provider

Create a function that returns a list of valid values:

```python
# myapp/providers.py
from config_loader import ProviderContext

def get_regions(ctx: ProviderContext) -> list[str]:
    """Return available AWS regions."""
    return [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
        "eu-central-1",
        "ap-southeast-1",
    ]
```

That's it! The builder pattern and error messages will use these values.

---

## Provider Context

Your function receives a `ProviderContext` with the current state:

```python
@dataclass
class ProviderContext:
    command_path: List[str]           # Current command path
    parsed_args: Dict[str, Any]       # Arguments parsed so far
    environment: Dict[str, str]       # Environment variables
    partial_value: Optional[str]      # Partial input (for completion)
```

### Context-Aware Providers

Use context to return different values based on other arguments:

```python
def get_instances(ctx: ProviderContext) -> list[str]:
    """Return instances filtered by region."""
    region = ctx.parsed_args.get("region")

    if region == "us-east-1":
        return ["i-abc123", "i-def456", "i-ghi789"]
    elif region == "eu-west-1":
        return ["i-eu001", "i-eu002"]
    else:
        return ["i-default"]
```

### Environment-Aware Providers

Read from environment for dynamic configuration:

```python
def get_clusters(ctx: ProviderContext) -> list[str]:
    """Return clusters from environment or default."""
    # Check for environment variable
    if "K8S_CLUSTERS" in ctx.environment:
        return ctx.environment["K8S_CLUSTERS"].split(",")

    # Default clusters
    return ["production", "staging", "development"]
```

---

## Autocompletion Support

Filter values for autocompletion using `partial_value`:

```python
def get_regions(ctx: ProviderContext) -> list[str]:
    """Return regions, filtered for autocompletion."""
    all_regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
    ]

    # Filter for autocompletion
    if ctx.partial_value:
        return [r for r in all_regions if r.startswith(ctx.partial_value)]

    return all_regions
```

### Using with the Builder

The builder pattern uses providers automatically:

```python
cfg = Configuration(spec)
builder = cfg.builder()
builder = builder.add_command("deploy")

# Get suggestions for region argument
arg_builder = builder.add_argument_builder("region")
suggestions = arg_builder.check_next()

print(suggestions.values)  # ["us-east-1", "us-west-2", ...]
print(suggestions.accepts_any)  # False (restricted to provider values)
```

---

## Fetching from External Sources

### API-Based Provider

Fetch values from an API:

```python
import requests
from functools import lru_cache

@lru_cache(maxsize=1)
def _fetch_regions_cached():
    """Fetch and cache regions from API."""
    response = requests.get("https://api.example.com/regions", timeout=5)
    return response.json()

def get_regions(ctx: ProviderContext) -> list[str]:
    """Return regions from API."""
    try:
        data = _fetch_regions_cached()
        regions = [r["name"] for r in data["regions"]]

        if ctx.partial_value:
            return [r for r in regions if r.startswith(ctx.partial_value)]
        return regions

    except Exception:
        # Fallback on error
        return ["us-east-1", "eu-west-1"]
```

### Database-Based Provider

Query a database for values:

```python
def get_projects(ctx: ProviderContext) -> list[str]:
    """Return projects from database."""
    import sqlite3

    conn = sqlite3.connect("projects.db")
    cursor = conn.execute("SELECT name FROM projects WHERE active = 1")
    projects = [row[0] for row in cursor.fetchall()]
    conn.close()

    if ctx.partial_value:
        return [p for p in projects if p.startswith(ctx.partial_value)]
    return projects
```

### File-Based Provider

Read from a configuration file:

```python
import json
from pathlib import Path

def get_environments(ctx: ProviderContext) -> list[str]:
    """Return environments from config file."""
    config_path = Path.home() / ".myapp" / "environments.json"

    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
            return data.get("environments", [])

    return ["development", "staging", "production"]
```

---

## Dependent Arguments

Use parsed arguments to create dependent dropdowns:

```yaml
arguments:
  - name: cloud
    type: string
    values_from: myapp.providers.get_clouds

  - name: region
    type: string
    values_from: myapp.providers.get_regions

  - name: instance-type
    type: string
    values_from: myapp.providers.get_instance_types
```

```python
def get_clouds(ctx: ProviderContext) -> list[str]:
    return ["aws", "gcp", "azure"]

def get_regions(ctx: ProviderContext) -> list[str]:
    """Return regions based on selected cloud."""
    cloud = ctx.parsed_args.get("cloud")

    regions = {
        "aws": ["us-east-1", "us-west-2", "eu-west-1"],
        "gcp": ["us-central1", "europe-west1", "asia-east1"],
        "azure": ["eastus", "westeurope", "southeastasia"],
    }

    return regions.get(cloud, [])

def get_instance_types(ctx: ProviderContext) -> list[str]:
    """Return instance types based on cloud and region."""
    cloud = ctx.parsed_args.get("cloud")
    region = ctx.parsed_args.get("region")

    if cloud == "aws" and region:
        # Different regions may have different instance types
        return ["t3.micro", "t3.small", "t3.medium", "m5.large"]
    elif cloud == "gcp":
        return ["e2-micro", "e2-small", "n1-standard-1"]
    elif cloud == "azure":
        return ["Standard_B1s", "Standard_B2s", "Standard_D2s_v3"]

    return []
```

---

## Performance Considerations

### Keep Providers Fast

For autocompletion, aim for <100ms response time:

```python
# Bad: Slow API call every time
def get_slow_regions(ctx: ProviderContext) -> list[str]:
    return requests.get("https://api.example.com/regions").json()

# Good: Cache results
@lru_cache(maxsize=1)
def _get_regions_cached():
    return requests.get("https://api.example.com/regions").json()

def get_regions(ctx: ProviderContext) -> list[str]:
    return _get_regions_cached()
```

### Limit Result Size

For large datasets, limit what you return:

```python
def get_users(ctx: ProviderContext) -> list[str]:
    """Return users, limited to 50 suggestions."""
    all_users = fetch_all_users()  # Might be thousands

    # Filter first
    if ctx.partial_value:
        filtered = [u for u in all_users if u.startswith(ctx.partial_value)]
        return filtered[:50]

    # Return most common/recent
    return sorted(all_users)[:50]
```

### Handle Failures Gracefully

Always handle errors to avoid breaking the CLI:

```python
def get_regions(ctx: ProviderContext) -> list[str]:
    """Return regions with fallback."""
    try:
        return fetch_regions_from_api()
    except requests.RequestException:
        # Return static fallback
        return ["us-east-1", "eu-west-1"]
    except Exception:
        # Empty list on unknown error
        return []
```

---

## Testing Providers

Test your providers work correctly:

```python
import pytest
from config_loader import ProviderContext
from myapp.providers import get_regions, get_instance_types

def test_get_regions_returns_values():
    ctx = ProviderContext()
    regions = get_regions(ctx)
    assert len(regions) > 0
    assert "us-east-1" in regions

def test_get_regions_filters_partial():
    ctx = ProviderContext(partial_value="us-")
    regions = get_regions(ctx)
    assert all(r.startswith("us-") for r in regions)

def test_get_instance_types_depends_on_cloud():
    ctx = ProviderContext(parsed_args={"cloud": "aws", "region": "us-east-1"})
    types = get_instance_types(ctx)
    assert "t3.micro" in types

def test_provider_handles_errors(mocker):
    mocker.patch("myapp.providers.fetch_regions_from_api", side_effect=Exception)
    ctx = ProviderContext()
    regions = get_regions(ctx)
    assert regions == ["us-east-1", "eu-west-1"]  # Fallback
```

---

## See Also

- **[Build Commands Programmatically](build-commands-programmatically.md)** — Using providers with builder
- **[YAML Schema Reference](../reference/yaml-schema.md)** — `values_from` field
- **[Python API Reference](../reference/python-api.md)** — `ProviderContext` class
