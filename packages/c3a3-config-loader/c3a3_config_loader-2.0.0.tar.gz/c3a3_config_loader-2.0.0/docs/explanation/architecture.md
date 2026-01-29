# Architecture

Understanding how config_loader components work together.

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Configuration                                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ ArgumentLoader│  │EnvironmentLoader│  │  RCLoader  │              │
│  │  (CLI args) │  │ (ENV vars)  │  │(~/.apprc)│                     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                         │
│         └────────────────┼────────────────┘                         │
│                          ▼                                          │
│                   ┌─────────────┐                                   │
│                   │   Merger    │◄─── Precedence rules              │
│                   └──────┬──────┘                                   │
│                          ▼                                          │
│         ┌────────────────┼────────────────┐                         │
│         ▼                ▼                ▼                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ TypeParser  │  │ Validator   │  │PluginManager│                 │
│  │  (parsing)  │  │(validation) │  │ (protocols) │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                         │
│         └────────────────┼────────────────┘                         │
│                          ▼                                          │
│                   ┌─────────────┐                                   │
│                   │ Encryption  │◄─── Obfuscation                   │
│                   └──────┬──────┘                                   │
│                          ▼                                          │
│               ┌───────────────────┐                                 │
│               │ ProcessingResult  │                                 │
│               └───────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Configuration

The main orchestrator class that coordinates all other components.

**Responsibilities:**
- Parse specification (YAML/JSON)
- Initialize loaders, validators, and plugins
- Coordinate the processing pipeline
- Provide access to results

**Key methods:**
- `process(args)` — Process configuration from all sources
- `validate(args)` — Validate without processing
- `builder()` — Create command builder (v2.0)
- `reveal()` — Decrypt obfuscated values

### Loaders

Three specialized loaders for different sources:

**ArgumentLoader** (`loaders.py`):
- Parses CLI arguments like `--namespace.name value`
- Handles short flags, boolean flags
- Extracts positional arguments

**EnvironmentLoader** (`loaders.py`):
- Reads `APPNAME_NAMESPACE_PARAM` environment variables
- Converts underscores to namespaces
- Handles type hints from spec

**RCLoader** (`loaders.py`):
- Loads `~/.appnamerc` TOML files
- Maps TOML sections to namespaces
- Preserves TOML types

### Validator

Validates both the spec and the resulting values.

**Spec validation:**
- Required fields present
- Valid types and values
- No naming conflicts
- Valid references

**Value validation:**
- Type matching
- Required fields provided
- Constraint satisfaction (accepts, min/max)
- Protocol requirements

### PluginManager

Handles protocol-based value loading.

**Responsibilities:**
- Register plugins by protocol
- Validate plugin manifests
- Route `protocol://value` to appropriate plugin
- Enforce type compatibility
- Check sensitivity requirements

### EncryptionManager

AES-256 encryption for obfuscated values.

**Process:**
1. Generate random key on startup
2. Encrypt with AES-256-CBC
3. Base64 encode with `obfuscated:` prefix
4. Decrypt on demand with `reveal()`

---

## v2.0 Command System

The v2.0 architecture adds command parsing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Configuration                                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     CommandParser                            │   │
│  │                                                             │   │
│  │  ┌───────────┐   ┌───────────┐   ┌───────────────────┐    │   │
│  │  │ Tokenizer │ → │ Phase 1:  │ → │ Phase 2:          │    │   │
│  │  │           │   │ Extract   │   │ Resolve command   │    │   │
│  │  │           │   │ globals   │   │ path              │    │   │
│  │  └───────────┘   └───────────┘   └─────────┬─────────┘    │   │
│  │                                            │              │   │
│  │                                            ▼              │   │
│  │                                  ┌───────────────────┐    │   │
│  │                                  │ Phase 3:          │    │   │
│  │                                  │ Bind arguments    │    │   │
│  │                                  └─────────┬─────────┘    │   │
│  │                                            │              │   │
│  │  ┌───────────────┐   ┌────────────────┐   │              │   │
│  │  │ExclusionValidator│◄──┤                  │◄──┘              │   │
│  │  └───────────────┘   │ CommandContext │                   │   │
│  │  ┌───────────────┐   │                │                   │   │
│  │  │CallableValidators│◄─┤                │                   │   │
│  │  └───────────────┘   └────────────────┘                   │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                          ┌───────────────┐                         │
│                          │CommandBuilder │◄─── Incremental building│
│                          └───────────────┘                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### CommandParser

Implements three-phase parsing (see [Three-Phase Parsing](three-phase-parsing.md)).

### Command Tree

Commands form a tree structure:

```
root
├── deploy (non-terminal)
│   ├── staging (terminal)
│   └── production (terminal)
└── rollback (terminal)
```

Each node has:
- Name and aliases
- Terminal flag
- Arguments (with scope)
- Exclusion groups
- Dependency rules
- Validators
- Subcommands

### CommandBuilder

Fluent API for incremental construction:

```python
builder = cfg.builder()
builder = builder.add_command("deploy")
builder = builder.add_argument("region", "us-east-1")
result = builder.build()
```

**Features:**
- Immutable builders (each method returns new instance)
- Suggestions at each step
- Value provider integration
- Validation before building

---

## Data Flow

### Processing Pipeline

```
Input (args: List[str])
         │
         ▼
┌──────────────────┐
│ 1. Load Sources  │
│   - CLI args     │
│   - ENV vars     │
│   - RC file      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Command Parse │  (v2.0 only)
│   - Tokenize     │
│   - Resolve path │
│   - Bind args    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Merge         │
│   - Precedence   │
│   - Defaults     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. Protocol Load │
│   - Parse URI    │
│   - Call plugin  │
│   - Validate     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. Parse Types   │
│   - string       │
│   - number       │
│   - boolean      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 6. Validate      │
│   - Required     │
│   - Accepts      │
│   - Min/Max      │
│   - Exclusions   │
│   - Dependencies │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 7. Obfuscate     │
│   - AES-256      │
│   - Base64       │
└────────┬─────────┘
         │
         ▼
ProcessingResult
```

### Result Structure

```python
ProcessingResult
├── config: ConfigurationResult
│   └── _config: Dict[namespace, Dict[name, value]]
│
├── command: CommandContext (v2.0)
│   ├── path: List[str]
│   ├── arguments: Dict[str, Any]
│   ├── positional: List[Any]
│   └── terminal: bool
│
├── warnings: List[str]
└── sources: Dict[str, str]
```

---

## Extension Points

### Protocol Plugins

Implement `ConfigPlugin` to add new protocols:

```python
class MyPlugin(ConfigPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(protocol="my", type="string")

    def load_value(self, value: str) -> str:
        return fetch_value(value)
```

### Value Providers

Functions that return valid values:

```python
def get_regions(ctx: ProviderContext) -> List[str]:
    return ["us-east-1", "eu-west-1"]
```

Referenced in spec:

```yaml
arguments:
  - name: region
    values_from: myapp.providers.get_regions
```

### Custom Validators

Functions for complex validation:

```python
def check_args(args: Dict, ctx: ValidatorContext) -> Optional[str]:
    if args.get("a") and args.get("b"):
        return "Cannot use --a with --b"
    return None
```

Referenced in spec:

```yaml
validators:
  - name: check
    rule: callable
    function: myapp.validators.check_args
```

---

## File Structure

```
src/config_loader/
├── __init__.py           # Public API exports
├── main.py               # Configuration class
├── models.py             # Data structures
├── result.py             # Result classes
├── loaders.py            # Source loaders
├── validator.py          # Spec validation
├── encryption.py         # AES-256 encryption
├── plugin_interface.py   # Plugin protocol
├── plugin_manager.py     # Plugin registry
├── command_parser.py     # Three-phase parser
├── tokenizer.py          # Token classification
├── exclusion_validator.py # Exclusion groups
├── callable_validators.py # Custom validators
├── value_provider.py     # Value providers
├── builder.py            # Command builder
├── deprecation.py        # Deprecation handling
├── error_recovery.py     # "Did you mean?"
├── serialization.py      # Export utilities
└── config_schema.json    # JSON Schema
```

---

## See Also

- **[Three-Phase Parsing](three-phase-parsing.md)** — How command parsing works
- **[Design Decisions](design-decisions.md)** — Why things work this way
- **[Python API Reference](../reference/python-api.md)** — All classes and methods
