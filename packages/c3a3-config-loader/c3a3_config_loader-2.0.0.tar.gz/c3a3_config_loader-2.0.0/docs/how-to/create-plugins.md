# How to Create Plugins

Build protocol plugins to load configuration values from external sources.

---

## Overview

Protocol plugins enable values like:

```bash
myapp --db.password vault://secrets/db/password
myapp --api.key ssm://prod/api/key
myapp --config file:///etc/myapp/config.json
```

Plugins handle the `protocol://value` syntax and return the actual value.

---

## Creating a Basic Plugin

### 1. Define the Plugin Class

Inherit from `ConfigPlugin`:

```python
from config_loader import ConfigPlugin, PluginManifest

class EnvPlugin(ConfigPlugin):
    """Load values from environment variables."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="env",
            type="string"
        )

    def load_value(self, protocol_value: str) -> str:
        """Load value from environment variable.

        Args:
            protocol_value: The part after 'env://' (variable name)

        Returns:
            The environment variable value

        Raises:
            ValueError: If variable is not set
        """
        import os

        value = os.environ.get(protocol_value)
        if value is None:
            raise ValueError(f"Environment variable '{protocol_value}' not set")
        return value
```

### 2. Register the Plugin

```python
from config_loader import Configuration

cfg = Configuration(spec, plugins=[EnvPlugin()])
```

### 3. Use in Configuration

```yaml
parameters:
  - namespace: db
    name: host
    type: string
```

```bash
myapp --db.host "env://DATABASE_HOST"
```

---

## Plugin Manifest

The manifest defines plugin metadata and constraints:

```python
@dataclass
class PluginManifest:
    protocol: str          # Protocol prefix (e.g., "vault")
    type: str = "string"   # Value type: "string", "number", "boolean"
    min_length: int = None # For strings: minimum length
    max_length: int = None # For strings: maximum length
    min_value: float = None # For numbers: minimum value
    max_value: float = None # For numbers: maximum value
    sensitive: bool = False # If True, requires obfuscated parameter
```

### Examples

```python
# String plugin with length constraints
PluginManifest(
    protocol="uuid",
    type="string",
    min_length=36,
    max_length=36
)

# Numeric plugin with range
PluginManifest(
    protocol="random",
    type="number",
    min_value=0,
    max_value=100
)

# Sensitive secret manager
PluginManifest(
    protocol="vault",
    type="string",
    sensitive=True  # Parameter must be obfuscated
)
```

---

## Real-World Examples

### HashiCorp Vault Plugin

```python
import hvac
from config_loader import ConfigPlugin, PluginManifest

class VaultPlugin(ConfigPlugin):
    """Load secrets from HashiCorp Vault."""

    def __init__(self, addr: str = None, token: str = None):
        import os
        self.addr = addr or os.environ.get("VAULT_ADDR", "http://localhost:8200")
        self.token = token or os.environ.get("VAULT_TOKEN")
        self._client = None

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="vault",
            type="string",
            sensitive=True  # Always obfuscate Vault secrets
        )

    @property
    def client(self):
        if self._client is None:
            self._client = hvac.Client(url=self.addr, token=self.token)
        return self._client

    def load_value(self, protocol_value: str) -> str:
        """Load secret from Vault.

        Args:
            protocol_value: Path like 'secrets/data/db/password#key'
                          or 'secrets/data/db/password' (uses 'value' key)
        """
        # Parse path and optional key
        if "#" in protocol_value:
            path, key = protocol_value.rsplit("#", 1)
        else:
            path, key = protocol_value, "value"

        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            data = response["data"]["data"]

            if key not in data:
                raise ValueError(f"Key '{key}' not found in secret '{path}'")

            return data[key]

        except hvac.exceptions.InvalidPath:
            raise ValueError(f"Secret not found: {path}")
        except Exception as e:
            raise ValueError(f"Failed to load secret: {e}")
```

Usage:

```yaml
parameters:
  - namespace: db
    name: password
    type: string
    protocol: vault
    obfuscated: true
```

```bash
myapp --db.password "vault://secrets/data/db/password#password"
```

### AWS SSM Plugin

```python
import boto3
from config_loader import ConfigPlugin, PluginManifest

class SSMPlugin(ConfigPlugin):
    """Load values from AWS Systems Manager Parameter Store."""

    def __init__(self, region: str = None):
        self.region = region
        self._client = None

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="ssm",
            type="string",
            sensitive=True
        )

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client("ssm", region_name=self.region)
        return self._client

    def load_value(self, protocol_value: str) -> str:
        """Load parameter from SSM.

        Args:
            protocol_value: Parameter name like '/prod/db/password'
        """
        try:
            response = self.client.get_parameter(
                Name=protocol_value,
                WithDecryption=True
            )
            return response["Parameter"]["Value"]

        except self.client.exceptions.ParameterNotFound:
            raise ValueError(f"SSM parameter not found: {protocol_value}")
        except Exception as e:
            raise ValueError(f"Failed to load SSM parameter: {e}")
```

### File Plugin

```python
import json
from pathlib import Path
from config_loader import ConfigPlugin, PluginManifest

class FilePlugin(ConfigPlugin):
    """Load values from files."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="file",
            type="string"
        )

    def load_value(self, protocol_value: str) -> str:
        """Load value from file.

        Args:
            protocol_value: File path, optionally with JSON key
                          '/path/to/file.json#key.nested'
        """
        # Parse path and optional key
        if "#" in protocol_value:
            file_path, json_path = protocol_value.rsplit("#", 1)
        else:
            file_path, json_path = protocol_value, None

        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")

        content = path.read_text()

        if json_path and path.suffix == ".json":
            data = json.loads(content)
            for key in json_path.split("."):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    raise ValueError(f"Key '{json_path}' not found in {file_path}")
            return str(data) if not isinstance(data, str) else data

        return content.strip()
```

---

## Constraint Validation

Plugins automatically validate constraints defined in the manifest:

```python
class PortPlugin(ConfigPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="port",
            type="number",
            min_value=1,
            max_value=65535
        )

    def load_value(self, protocol_value: str) -> int:
        return int(protocol_value)
```

```bash
myapp --server.port "port://99999"
# Error: Value 99999 exceeds maximum 65535
```

The `validate_constraints` method is called automatically after `load_value`.

---

## Sensitive Plugins

Mark plugins as sensitive when they return secrets:

```python
@property
def manifest(self) -> PluginManifest:
    return PluginManifest(
        protocol="vault",
        type="string",
        sensitive=True   # <-- Requires obfuscated parameter
    )
```

When `sensitive=True`:
- The parameter **must** have `obfuscated: true`
- The returned value is encrypted in memory
- Help text shows `[sensitive]` indicator

---

## Registering Multiple Plugins

```python
cfg = Configuration(
    spec,
    plugins=[
        VaultPlugin(),
        SSMPlugin(region="us-east-1"),
        FilePlugin(),
        EnvPlugin(),
    ]
)
```

Each protocol can only have one plugin registered.

---

## Error Handling

Raise `ValueError` with descriptive messages:

```python
def load_value(self, protocol_value: str) -> str:
    if not protocol_value:
        raise ValueError("Protocol value cannot be empty")

    try:
        return self._fetch(protocol_value)
    except ConnectionError:
        raise ValueError(f"Could not connect to secret store")
    except PermissionError:
        raise ValueError(f"Access denied to secret: {protocol_value}")
    except Exception as e:
        raise ValueError(f"Failed to load secret '{protocol_value}': {e}")
```

config_loader catches `ValueError` and provides context about which parameter failed.

---

## Testing Plugins

```python
import pytest
from config_loader import Configuration
from myapp.plugins import VaultPlugin

def test_vault_plugin_loads_secret(mocker):
    # Mock Vault client
    mock_client = mocker.MagicMock()
    mock_client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"password": "secret123"}}
    }

    plugin = VaultPlugin()
    mocker.patch.object(plugin, "client", mock_client)

    result = plugin.load_value("secrets/data/db/password#password")
    assert result == "secret123"


def test_vault_plugin_raises_on_missing():
    plugin = VaultPlugin()

    with pytest.raises(ValueError, match="not found"):
        plugin.load_value("nonexistent/path")


def test_plugin_integration():
    class MockPlugin(ConfigPlugin):
        @property
        def manifest(self):
            return PluginManifest(protocol="mock", type="string")

        def load_value(self, value):
            return f"loaded:{value}"

    spec = {
        "app_name": "test",
        "parameters": [
            {"namespace": "db", "name": "host", "type": "string"}
        ]
    }

    cfg = Configuration(spec, plugins=[MockPlugin()])
    result = cfg.process(["--db.host", "mock://test-value"])

    assert result.db.host == "loaded:test-value"
```

---

## See Also

- **[Handle Secrets](handle-secrets.md)** — Using obfuscation
- **[Python API Reference](../reference/python-api.md)** — `ConfigPlugin` class
- **[YAML Schema Reference](../reference/yaml-schema.md)** — `protocol` field
