# How to Handle Secrets

Protect sensitive configuration values with encryption and obfuscation.

---

## Overview

config_loader provides two mechanisms for handling secrets:

1. **Obfuscation**: Encrypt values in memory using AES-256
2. **Protocol plugins**: Load secrets from external sources (vault, SSM, etc.)

---

## Memory Obfuscation

### Mark Parameters as Obfuscated

```yaml
parameters:
  - namespace: db
    name: password
    type: string
    obfuscated: true    # Encrypt in memory
```

When `obfuscated: true`, the value is encrypted immediately after loading and stays encrypted in the result object.

### Accessing Obfuscated Values

Obfuscated values appear as `obfuscated:...` strings:

```python
result = cfg.process(["--db.password", "secret123"])

# Direct access returns encrypted value
print(result.db.password)
# obfuscated:YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=...

# Use reveal() to decrypt
password = cfg.reveal(result.db.password)
print(password)  # "secret123"
```

### How Obfuscation Works

1. A random AES-256 key is generated when `Configuration` is created
2. Values marked `obfuscated: true` are encrypted using AES-256-CBC
3. The encrypted value is base64-encoded with an `obfuscated:` prefix
4. The key exists only in memory and is never persisted
5. Use `cfg.reveal()` to decrypt when needed

This prevents secrets from appearing in:
- Logs and debug output
- Stack traces
- Memory dumps (without the key)
- Accidental print statements

---

## Using Protocol Plugins

For secrets stored externally, use protocol plugins:

### Vault Example

```yaml
parameters:
  - namespace: db
    name: password
    type: string
    protocol: vault      # Must use vault:// prefix
    obfuscated: true     # Required for sensitive protocols
```

```bash
myapp --db.password "vault://secrets/db/password"
```

### AWS SSM Example

```yaml
parameters:
  - namespace: api
    name: key
    type: string
    protocol: ssm
    obfuscated: true
```

```bash
myapp --api.key "ssm://prod/api/key"
```

### Protocol Enforcement

When `protocol` is set, config_loader enforces that values use that protocol:

```bash
# Error: Parameter db.password requires protocol 'vault' but got non-protocol value
myapp --db.password "plaintext"

# OK: Uses vault protocol
myapp --db.password "vault://secrets/db/password"
```

---

## Sensitive Protocols

Plugins can declare themselves as sensitive:

```python
class VaultPlugin(ConfigPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="vault",
            type="string",
            sensitive=True   # <-- Indicates sensitive data
        )
```

When using a sensitive protocol, the parameter **must** be marked `obfuscated`:

```yaml
# Error: Parameter db.password must be obfuscated when using sensitive protocol 'vault'
parameters:
  - namespace: db
    name: password
    protocol: vault
    # Missing: obfuscated: true
```

---

## Best Practices

### 1. Never Log Secrets

```python
result = cfg.process(args)

# Bad: May leak secrets
print(f"Config: {result.export_dict()}")

# Good: Obfuscated values are encrypted
print(f"Password: {result.db.password}")  # Shows "obfuscated:..."

# Good: Only reveal when needed
conn = connect(
    host=result.db.host,
    password=cfg.reveal(result.db.password)
)
```

### 2. Use Environment Variables for Secrets

```bash
# Don't put secrets in command line (visible in process list)
myapp --db.password "secret123"   # Bad

# Use environment variables
export MYAPP_DB_PASSWORD="secret123"
myapp                             # Good
```

### 3. Use Protocol Plugins for Production

```yaml
# Development: direct values (obfuscated)
parameters:
  - namespace: db
    name: password
    obfuscated: true

# Production: external secret manager
parameters:
  - namespace: db
    name: password
    protocol: vault
    obfuscated: true
```

### 4. Rotate Keys in Long-Running Processes

The encryption key is generated per `Configuration` instance:

```python
# For long-running services, recreate Configuration periodically
cfg = Configuration(spec)  # New key generated

# After key rotation:
cfg = Configuration(spec)  # New key, old obfuscated values invalid
```

---

## Serialization and Secrets

### Filtering Sensitive Values

When exporting results, filter out secrets:

```python
from config_loader import filter_sensitive_values

result = cfg.process(args)

# Filter obfuscated values before logging
safe_data = filter_sensitive_values(result.to_dict())
print(json.dumps(safe_data, indent=2))
```

### Creating Replay Files

The `create_replay_file` function automatically excludes sensitive values:

```python
from config_loader import create_replay_file

# Obfuscated values are replaced with placeholders
create_replay_file(result, "/path/to/replay.json")
```

---

## Testing with Secrets

### Mock Obfuscation in Tests

```python
def test_with_secrets(monkeypatch):
    spec = {
        "app_name": "test",
        "parameters": [
            {"namespace": "db", "name": "password", "type": "string", "obfuscated": True}
        ]
    }

    cfg = Configuration(spec)
    result = cfg.process(["--db.password", "test-secret"])

    # Value is obfuscated
    assert result.db.password.startswith("obfuscated:")

    # Can be revealed
    assert cfg.reveal(result.db.password) == "test-secret"
```

### Mock Protocol Plugins

```python
def test_with_protocol_plugin(monkeypatch):
    class MockVaultPlugin(ConfigPlugin):
        @property
        def manifest(self):
            return PluginManifest(protocol="vault", type="string", sensitive=True)

        def load_value(self, protocol_value):
            # Return mock secret
            return "mocked-secret"

    spec = {
        "app_name": "test",
        "parameters": [
            {"namespace": "db", "name": "password", "type": "string",
             "protocol": "vault", "obfuscated": True}
        ]
    }

    cfg = Configuration(spec, plugins=[MockVaultPlugin()])
    result = cfg.process(["--db.password", "vault://any/path"])

    # Plugin returned mock value, which is then obfuscated
    assert cfg.reveal(result.db.password) == "mocked-secret"
```

---

## Troubleshooting

### "Value is not obfuscated" Error

```python
cfg.reveal("plaintext")
# ValueError: Value is not obfuscated (missing 'obfuscated:' prefix)
```

Only values returned by config_loader with `obfuscated: true` can be revealed.

### "Failed to decrypt value" Error

```python
# Using obfuscated value from different Configuration instance
cfg1 = Configuration(spec)
result1 = cfg1.process(args)

cfg2 = Configuration(spec)  # Different encryption key!
cfg2.reveal(result1.db.password)  # Fails
```

Each `Configuration` has its own encryption key. Only reveal values using the same instance that processed them.

---

## See Also

- **[Create Plugins](create-plugins.md)** — Build protocol plugins
- **[YAML Schema Reference](../reference/yaml-schema.md)** — `obfuscated` field
- **[Python API Reference](../reference/python-api.md)** — `reveal()` method
