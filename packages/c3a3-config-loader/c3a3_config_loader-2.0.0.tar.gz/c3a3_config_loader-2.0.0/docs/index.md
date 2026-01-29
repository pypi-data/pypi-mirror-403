# config_loader Documentation

**Seamless, pluggable configuration for Python apps** — merge CLI, environment variables, and RC files with validation, encryption, and hierarchical commands.

---

## Quick Navigation

### [Tutorials](tutorials/quickstart.md)
*Learning-oriented guides to get you started*

- **[Quickstart](tutorials/quickstart.md)** — Your first config in 5 minutes
- **[Building a CLI App](tutorials/cli-app.md)** — Create a multi-command application
- **[Migrating to v2.0](tutorials/migration-v1-to-v2.md)** — Upgrade from v1.x

### [How-To Guides](how-to/validate-inputs.md)
*Task-oriented guides for specific goals*

- **[Validate Inputs](how-to/validate-inputs.md)** — Required fields, exclusion groups, dependencies
- **[Use Value Providers](how-to/use-value-providers.md)** — Dynamic suggestions and autocompletion
- **[Build Commands Programmatically](how-to/build-commands-programmatically.md)** — The builder pattern
- **[Handle Secrets](how-to/handle-secrets.md)** — Encryption and obfuscation
- **[Create Plugins](how-to/create-plugins.md)** — Protocol-based value loading

### [Reference](reference/yaml-schema.md)
*Technical reference material*

- **[YAML Schema](reference/yaml-schema.md)** — Complete configuration schema
- **[Python API](reference/python-api.md)** — Classes, methods, and signatures
- **[CLI Conventions](reference/cli-conventions.md)** — Argument syntax and precedence

### [Explanation](explanation/architecture.md)
*Understanding-oriented discussion*

- **[Architecture](explanation/architecture.md)** — Components and data flow
- **[Three-Phase Parsing](explanation/three-phase-parsing.md)** — How command parsing works
- **[Design Decisions](explanation/design-decisions.md)** — Why things work this way

---

## What is config_loader?

config_loader is a Python library that unifies configuration from multiple sources:

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  CLI Args   │   │  ENV Vars   │   │  RC File    │
│ --db.host   │   │ APP_DB_HOST │   │ ~/.apprc    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────┬────┴────────────────┘
                    ▼
            ┌───────────────┐
            │ config_loader │
            │   • Merge     │
            │   • Validate  │
            │   • Encrypt   │
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │    Result     │
            │ result.db.host│
            └───────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-source** | CLI arguments, environment variables, RC files |
| **Precedence** | Configurable priority (args > env > rc) |
| **Validation** | Types, required fields, ranges, allowed values |
| **Commands** | Hierarchical command system (v2.0) |
| **Value Providers** | Dynamic suggestions for arguments |
| **Encryption** | AES-256 obfuscation for secrets |
| **Plugins** | Protocol-based value loading (vault://, ssm://) |
| **Builder Pattern** | Programmatic command construction |

### Version History

- **v2.0** — Hierarchical command system, value providers, builder pattern
- **v1.x** — Parameter-based configuration with validation and encryption

---

## Installation

```bash
pip install c3a3-config-loader
```

Requires Python 3.11+.

---

## Quick Example

### v1.x Style (Parameters Only)

```python
from config_loader import Configuration

spec = {
    "app_name": "myapp",
    "parameters": [
        {"namespace": "db", "name": "host", "type": "string", "required": True},
        {"namespace": "db", "name": "port", "type": "number", "default": 5432},
    ]
}

cfg = Configuration(spec)
result = cfg.process()  # Reads CLI, ENV, RC file

print(result.db.host)  # "localhost"
print(result.db.port)  # 5432
```

### v2.0 Style (With Commands)

```python
from config_loader import Configuration

spec = {
    "schema_version": "2.0",
    "app_name": "myapp",
    "commands": [
        {
            "name": "deploy",
            "terminal": True,
            "arguments": [
                {"name": "environment", "type": "string", "required": True},
                {"name": "force", "type": "boolean", "short": "f"},
            ]
        }
    ]
}

cfg = Configuration(spec)
result = cfg.process(["deploy", "--environment", "prod", "-f"])

print(result.command.path)       # ["deploy"]
print(result.command.arguments)  # {"environment": "prod", "force": True}
```

---

## Getting Help

- **Examples**: See the [examples/](../examples/) directory
- **Issues**: [GitHub Issues](https://github.com/your-org/c3a3-config-loader/issues)
- **Source**: [GitHub Repository](https://github.com/your-org/c3a3-config-loader)

---

*Documentation follows the [Divio documentation system](https://documentation.divio.com/).*
