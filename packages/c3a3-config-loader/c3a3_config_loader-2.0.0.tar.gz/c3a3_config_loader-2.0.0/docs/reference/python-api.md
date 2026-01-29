# Python API Reference

Complete reference for config_loader Python classes and functions.

---

## Quick Reference

```python
from config_loader import (
    # Core
    Configuration,
    load_config,
    load_configs,

    # Results
    ProcessingResult,
    ConfigurationResult,
    CommandContext,

    # Models
    ConfigParam,
    ConfigArg,
    Command,
    CommandArgument,

    # Builder Pattern
    CommandBuilder,
    Suggestions,
    ArgumentSuggestion,
    CommandSuggestion,

    # Plugins
    ConfigPlugin,
    PluginManifest,
)
```

---

## Configuration

The main orchestrator class.

### Constructor

```python
Configuration(spec: Dict[str, Any], plugins: Optional[List[ConfigPlugin]] = None)
```

**Parameters:**
- `spec`: Configuration specification dictionary
- `plugins`: Optional list of protocol plugins

**Example:**

```python
from config_loader import Configuration

spec = {
    "schema_version": "2.0",
    "app_name": "myapp",
    "parameters": [
        {"namespace": "db", "name": "host", "type": "string", "required": True}
    ],
    "commands": [
        {"name": "deploy", "terminal": True}
    ]
}

cfg = Configuration(spec)
```

### Methods

#### `process(args: List[str]) -> ProcessingResult`

Process configuration from all sources.

```python
result = cfg.process(["deploy", "--db.host", "localhost"])

# Access global parameters
print(result.db.host)  # "localhost"

# Access command info (v2.0)
print(result.command.path)       # ["deploy"]
print(result.command.arguments)  # {}
```

#### `validate(args: List[str]) -> bool`

Validate configuration without processing.

```python
if cfg.validate(["deploy", "--db.host", "localhost"]):
    print("Configuration is valid")
```

#### `register_plugin(plugin: ConfigPlugin) -> None`

Register a protocol plugin.

```python
cfg.register_plugin(my_vault_plugin)
```

#### `reveal(obfuscated_value: str) -> str`

Decrypt an obfuscated value.

```python
secret = cfg.reveal(result.db.password)
```

#### `builder() -> CommandBuilder`

Create a command builder for incremental construction (v2.0).

```python
builder = cfg.builder()
suggestions = builder.check_next()
```

#### `print_help(command_path: Optional[List[str]] = None) -> None`

Print CLI help information.

```python
cfg.print_help()                      # Root help
cfg.print_help(["deploy", "staging"]) # Command-specific help
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `app_name` | `str` | Application name from spec |
| `schema_version` | `str` | Schema version ("1.0" or "2.0") |
| `parameters` | `List[ConfigParam]` | Parsed parameters |
| `commands` | `List[Command]` | Parsed commands (v2.0) |
| `precedence` | `List[str]` | Source precedence order |

---

## ProcessingResult

Combined result with config and command context (v2.0).

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `config` | `ConfigurationResult` | Processed configuration |
| `command` | `Optional[CommandContext]` | Command context (None if no commands) |
| `warnings` | `List[str]` | Deprecation warnings |
| `sources` | `Dict[str, str]` | Parameter-to-source mapping |

### Methods

#### `to_dict() -> Dict[str, Any]`

Export result as a dictionary.

```python
data = result.to_dict()
# {
#     "schema_version": "2.0",
#     "config": {"db": {"host": "localhost"}},
#     "command": {"path": ["deploy"], "arguments": {}, ...},
#     "sources": {"db.host": "args"}
# }
```

#### `to_json(indent: int = 2) -> str`

Export result as JSON string.

```python
json_str = result.to_json()
```

#### `from_dict(data: Dict[str, Any]) -> ProcessingResult` (classmethod)

Reconstruct from a dictionary.

```python
result = ProcessingResult.from_dict(saved_data)
```

#### `debug() -> None`

Print debug information.

```python
result.debug()
# Processing Result Debug Information:
# ==================================================
# Configuration Sources:
# db.host: localhost (from args)
# ...
```

### Attribute Access

For backward compatibility, attribute access delegates to `ConfigurationResult`:

```python
# These are equivalent:
result.db.host
result.config.db.host
```

---

## ConfigurationResult

Processed configuration values (v1.x style).

### Methods

#### `export_dict() -> Dict[str, Any]`

Export as dictionary.

```python
config_dict = result.config.export_dict()
# {"db": {"host": "localhost", "port": 5432}}
```

#### `export_json() -> str`

Export as JSON string.

```python
json_str = result.config.export_json()
```

#### `debug() -> None`

Print debug information about sources.

### Attribute Access

Parameters are accessible via dot notation:

```python
result.db.host      # Namespaced parameter
result.debug        # Non-namespaced parameter (namespace: null)
result.arguments.input_file  # Positional argument
```

---

## CommandContext

Result of command path resolution (v2.0).

```python
@dataclass
class CommandContext:
    path: List[str]              # e.g., ["deploy", "staging"]
    arguments: Dict[str, Any]    # e.g., {"region": "us-east-1"}
    positional: List[Any]        # Positional args after command
    terminal: bool               # Whether command is terminal
```

**Example:**

```python
result = cfg.process(["deploy", "staging", "--region", "us-east-1"])

print(result.command.path)       # ["deploy", "staging"]
print(result.command.arguments)  # {"region": "us-east-1"}
print(result.command.terminal)   # True
```

---

## CommandBuilder

Builder for incremental command construction.

### Methods

#### `check_next() -> Suggestions`

Check what can be added next.

```python
suggestions = builder.check_next()
print(suggestions.is_valid)    # Can we build now?
print(suggestions.commands)    # Available subcommands
print(suggestions.arguments)   # Available arguments
print(suggestions.errors)      # Any validation errors
```

#### `add_command(name: str) -> CommandBuilder`

Add a command or subcommand.

```python
builder = builder.add_command("deploy")
builder = builder.add_command("staging")  # Subcommand
```

#### `add_argument(name: str, value: Optional[Any] = None) -> CommandBuilder`

Add an argument.

```python
builder = builder.add_argument("region", "us-east-1")
builder = builder.add_argument("force")  # Boolean flag (True)
```

#### `add_argument_builder(name: str) -> ArgumentValueBuilder`

Get a builder for setting an argument with value suggestions.

```python
arg_builder = builder.add_argument_builder("region")
suggestions = arg_builder.check_next()
print(suggestions.values)  # ["us-east-1", "eu-west-1", ...]

arg_builder.set_value("us-east-1")
builder = arg_builder.build()
```

#### `add_positional(value: Any) -> CommandBuilder`

Add a positional argument.

```python
builder = builder.add_positional("filename.txt")
```

#### `build() -> ProcessingResult`

Build the final result.

```python
result = builder.build()
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `command_path` | `List[str]` | Current command path |
| `arguments` | `Dict[str, Any]` | Currently set arguments |
| `positional` | `List[Any]` | Currently set positional args |

---

## Suggestions

Result of `builder.check_next()`.

```python
@dataclass
class Suggestions:
    is_valid: bool                           # Can build now?
    commands: List[CommandSuggestion]        # Available subcommands
    arguments: List[ArgumentSuggestion]      # Available arguments
    positional_expected: bool                # Expect positional args?
    errors: List[str]                        # Validation errors
```

---

## CommandSuggestion

Suggestion for a command.

```python
@dataclass
class CommandSuggestion:
    name: str                    # Command name
    aliases: List[str]           # Alternative names
    description: Optional[str]   # Human-readable description
    terminal: bool               # Is terminal command?
```

---

## ArgumentSuggestion

Suggestion for an argument.

```python
@dataclass
class ArgumentSuggestion:
    name: str                          # Argument name
    short: Optional[str]               # Short flag (e.g., "r")
    arg_type: str                      # string, number, boolean
    required: bool                     # Is required?
    description: Optional[str]         # Description
    expects_value: bool                # Needs a value?
    default: Any                       # Default value
    value_suggestions: List[str]       # Suggested values
```

---

## Model Classes

### ConfigParam

Parameter definition.

```python
@dataclass
class ConfigParam:
    namespace: Optional[str]      # Grouping namespace
    name: str                     # Parameter name
    type: str                     # string, number, boolean
    required: bool = False        # Must be provided
    default: Any = None           # Default value
    accepts: Optional[List[Any]] = None  # Allowed values
    obfuscated: bool = False      # Encrypt in memory
    protocol: Optional[str] = None  # Protocol for loading
```

### ConfigArg

Positional argument definition.

```python
@dataclass
class ConfigArg:
    name: str                     # Argument name
    type: str                     # string, number, boolean
    required: bool = False        # Must be provided
    default: Any = None           # Default value
    protocol: Optional[str] = None  # Protocol for loading
```

### Command

Command definition (v2.0).

```python
@dataclass
class Command:
    name: str                                  # Command name
    aliases: List[str]                         # Alternative names
    terminal: bool = False                     # Executable?
    ordering: str = "relaxed"                  # Argument ordering
    arguments: List[CommandArgument]           # Command arguments
    exclusion_groups: List[ExclusionGroup]     # Mutually exclusive
    dependency_rules: List[DependencyRule]     # Dependencies
    validators: List[Dict[str, Any]]           # Custom validators
    subcommands: List[Command]                 # Child commands
    deprecated: Optional[Deprecation] = None   # Deprecation info
```

### CommandArgument

Argument definition (v2.0).

```python
@dataclass
class CommandArgument:
    name: str                             # Argument name
    type: str = "string"                  # string, number, boolean
    short: Optional[str] = None           # Short flag
    scope: str = "local"                  # local, inherited, ephemeral
    required: bool = False                # Must be provided
    default: Any = None                   # Default value
    env: bool = False                     # Read from env vars
    env_name: Optional[str] = None        # Custom env var name
    nargs: Optional[str] = None           # Argument count
    deprecated: Optional[Deprecation] = None
    values_from: Optional[str] = None     # Value provider path
```

---

## Plugin Interface

### ConfigPlugin (Protocol)

```python
class ConfigPlugin(Protocol):
    def get_manifest(self) -> PluginManifest:
        """Return plugin manifest."""
        ...

    def load_value(self, value: str, expected_type: str) -> Any:
        """Load a value using this plugin's protocol."""
        ...
```

### PluginManifest

```python
@dataclass
class PluginManifest:
    protocol: str          # Protocol prefix (e.g., "vault")
    type: str              # Type of values (e.g., "secret")
    sensitive: bool = False  # Requires obfuscation
```

**Example plugin:**

```python
from config_loader import ConfigPlugin, PluginManifest

class VaultPlugin:
    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            protocol="vault",
            type="secret",
            sensitive=True
        )

    def load_value(self, value: str, expected_type: str) -> Any:
        # value is the part after "vault://"
        return fetch_from_vault(value)

# Register
cfg = Configuration(spec, plugins=[VaultPlugin()])

# Use in config
# db.password: "vault://secrets/db/password"
```

---

## Utility Functions

### load_config

Load configuration from a file object.

```python
from config_loader import load_config

with open("config.json") as f:
    cfg = load_config(f)
```

### load_configs

Load configuration from a dictionary.

```python
from config_loader import load_configs

spec = {"app_name": "myapp", ...}
cfg = load_configs(spec)
```

---

## Serialization Functions

### to_json_safe

Convert result to JSON-safe dictionary.

```python
from config_loader import to_json_safe

data = to_json_safe(result)
```

### to_yaml

Convert result to YAML string.

```python
from config_loader import to_yaml

yaml_str = to_yaml(result)
```

### create_replay_file / load_replay_file

Save and restore execution state.

```python
from config_loader import create_replay_file, load_replay_file

# Save
create_replay_file(result, "/path/to/replay.json")

# Restore
restored = load_replay_file("/path/to/replay.json")
```

---

## Exceptions

| Exception | Description |
|-----------|-------------|
| `ValueError` | Invalid configuration or arguments |
| `FileNotFoundError` | Config file not found |
| `ImportError` | Missing optional dependency (pyyaml, jsonschema) |
| `ValidatorError` | Custom validator failed |
| `DeprecationError` | Deprecated item used in strict mode |

---

## See Also

- **[YAML Schema Reference](yaml-schema.md)** — Configuration options
- **[CLI Conventions](cli-conventions.md)** — Argument syntax
- **[Build Commands Programmatically](../how-to/build-commands-programmatically.md)** — Builder tutorial
