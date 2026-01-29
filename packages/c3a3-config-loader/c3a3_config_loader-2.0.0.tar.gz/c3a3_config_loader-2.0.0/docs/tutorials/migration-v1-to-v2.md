# Migrating from v1.x to v2.0

This guide helps you upgrade from config_loader v1.x to v2.0.

## Good News: Full Backward Compatibility

**Your v1.x specs work unchanged.** You don't need to migrate anything unless you want the new features.

```yaml
# This v1.x spec still works perfectly in v2.0
app_name: myapp
precedence: [args, env, rc]
parameters:
  - namespace: db
    name: host
    type: string
```

## What's New in v2.0

| Feature | v1.x | v2.0 |
|---------|------|------|
| Parameters (CLI/ENV/RC) | ✓ | ✓ |
| Hierarchical Commands | ✗ | ✓ |
| Subcommands | ✗ | ✓ |
| Command Arguments | ✗ | ✓ |
| Exclusion Groups | ✗ | ✓ |
| Dependency Rules | ✗ | ✓ |
| Value Providers | ✗ | ✓ |
| Builder Pattern | ✗ | ✓ |
| Deprecation Warnings | ✗ | ✓ |

## Schema Version

v2.0 specs should declare their schema version:

```yaml
schema_version: "2.0"    # <-- Add this
app_name: myapp
commands:
  - name: deploy
    terminal: true
```

v1.x specs can omit it (defaults to "1.0") or explicitly set it:

```yaml
schema_version: "1.0"    # Optional for v1.x
app_name: myapp
parameters:
  - namespace: db
    name: host
```

## Result Object Changes

### v1.x: ConfigurationResult

```python
result = cfg.process()

# Access parameters directly
print(result.db.host)
print(result.mode)
```

### v2.0: ProcessingResult

```python
result = cfg.process()

# For v1.x-style specs (no commands), same access pattern
print(result.db.host)      # Still works!
print(result.mode)         # Still works!

# For v2.0 specs with commands
print(result.command.path)        # ["deploy", "staging"]
print(result.command.arguments)   # {"region": "us-east-1"}
print(result.command.terminal)    # True
```

The key difference: v2.0 adds a `command` attribute for command information.

## Combining Parameters and Commands

You can use both in the same spec:

```yaml
schema_version: "2.0"
app_name: myapp

# Global parameters (v1.x style)
parameters:
  - namespace: null
    name: verbose
    type: boolean
    default: false

# Commands (v2.0 style)
commands:
  - name: deploy
    terminal: true
    arguments:
      - name: region
        type: string
```

Usage:

```bash
myapp --verbose deploy --region us-east-1
```

Access:

```python
result = cfg.process()

# Global parameters
print(result.verbose)              # True

# Command info
print(result.command.path)         # ["deploy"]
print(result.command.arguments)    # {"region": "us-east-1"}
```

## Converting Parameters to Commands

If you want to convert a flat v1.x app to use commands:

### Before (v1.x)

```yaml
app_name: myapp
parameters:
  - namespace: null
    name: action
    type: string
    accepts: [deploy, rollback]

  - namespace: null
    name: region
    type: string
```

```python
result = cfg.process()
if result.action == "deploy":
    deploy(result.region)
elif result.action == "rollback":
    rollback(result.region)
```

### After (v2.0)

```yaml
schema_version: "2.0"
app_name: myapp

commands:
  - name: deploy
    terminal: true
    arguments:
      - name: region
        type: string

  - name: rollback
    terminal: true
    arguments:
      - name: region
        type: string
```

```python
result = cfg.process()
command = result.command.path[0]

if command == "deploy":
    deploy(result.command.arguments.get("region"))
elif command == "rollback":
    rollback(result.command.arguments.get("region"))
```

Benefits:
- Better CLI UX (`myapp deploy` vs `myapp --action deploy`)
- Subcommand-specific arguments
- Validation per command
- Help text per command

## New Features to Consider

### Value Providers

Add dynamic suggestions to arguments:

```yaml
arguments:
  - name: region
    type: string
    values_from: myapp.providers.get_regions
```

### Exclusion Groups

Prevent conflicting options:

```yaml
exclusion_groups:
  - name: output-format
    arguments: [json, yaml, table]
    message: "Choose one output format"
```

### Dependency Rules

Require related options together:

```yaml
dependency_rules:
  - name: auth-complete
    rule: if_then
    if_arg: username
    then_require: [password]
```

### Builder Pattern

Programmatically construct commands:

```python
builder = cfg.builder()
builder = builder.add_command("deploy")

# Get suggestions
suggestions = builder.check_next()
print(suggestions.arguments)  # Available arguments

# Build incrementally
builder = builder.add_argument("region", "us-east-1")
result = builder.build()
```

## Deprecation Warnings

Mark old commands/arguments as deprecated:

```yaml
commands:
  - name: old-deploy
    deprecated:
      since: "2.0"
      replacement: "deploy"
      message: "Use 'deploy' instead"
```

Users see warnings but commands still work:

```
Warning: 'old-deploy' is deprecated since 2.0. Use 'deploy' instead.
```

## Testing Your Migration

1. **Run existing tests** — They should pass unchanged
2. **Check process() output** — Verify result structure
3. **Test CLI invocations** — Ensure same behavior
4. **Add command tests** — If using new features

```python
# Test backward compatibility
def test_v1_style_still_works():
    spec = {"app_name": "test", "parameters": [...]}
    cfg = Configuration(spec)
    result = cfg.process(["--host", "localhost"])
    assert result.host == "localhost"

# Test new v2.0 features
def test_v2_commands():
    spec = {"schema_version": "2.0", "commands": [...]}
    cfg = Configuration(spec)
    result = cfg.process(["deploy", "--region", "us-east-1"])
    assert result.command.path == ["deploy"]
```

## Next Steps

- **[Building a CLI App](cli-app.md)** — Full v2.0 tutorial
- **[YAML Schema Reference](../reference/yaml-schema.md)** — All new options
- **[Architecture](../explanation/architecture.md)** — How it all fits together
