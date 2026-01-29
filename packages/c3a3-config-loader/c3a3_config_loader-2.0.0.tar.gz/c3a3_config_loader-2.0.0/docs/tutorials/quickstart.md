# Quickstart

Get config_loader working in 5 minutes.

## Installation

```bash
pip install c3a3-config-loader
```

## Step 1: Create a Configuration File

Create `myapp.yaml` in your project directory:

```yaml
schema_version: "1.0"
app_name: myapp
precedence:
  - args    # CLI arguments (highest priority)
  - env     # Environment variables
  - rc      # RC file (~/.myapprc)

parameters:
  - namespace: db
    name: host
    type: string
    required: true

  - namespace: db
    name: port
    type: number
    default: 5432

  - namespace: null
    name: debug
    type: boolean
    default: false
```

## Step 2: Load Configuration in Python

Create `myapp.py`:

```python
from config_loader import load_config

# Load from myapp.yaml (auto-detected from script name)
cfg = load_config("myapp.yaml")

# Process all sources (CLI, ENV, RC file)
result = cfg.process()

# Access values with dot notation
print(f"Database: {result.db.host}:{result.db.port}")
print(f"Debug mode: {result.debug}")
```

## Step 3: Run Your App

### Using CLI arguments

```bash
python myapp.py --db.host localhost --debug
```

Output:
```
Database: localhost:5432
Debug mode: True
```

### Using environment variables

```bash
export MYAPP_DB_HOST=production-db.example.com
export MYAPP_DB_PORT=5433
python myapp.py
```

Output:
```
Database: production-db.example.com:5433
Debug mode: False
```

### Using an RC file

Create `~/.myapprc`:

```toml
[db]
host = "dev-db.local"
port = 5432

[default]
debug = true
```

Then run without arguments:

```bash
python myapp.py
```

## Step 4: Understand Precedence

The `precedence` field controls which source wins when values conflict:

```yaml
precedence:
  - args    # Checked first (wins if present)
  - env     # Checked second
  - rc      # Checked last (fallback)
```

Example with all sources:

```bash
# RC file has: db.host = "rc-host"
# ENV has: MYAPP_DB_HOST=env-host
# CLI has: --db.host cli-host

python myapp.py --db.host cli-host
# Result: result.db.host = "cli-host" (CLI wins)

python myapp.py
# Result: result.db.host = "env-host" (ENV wins, no CLI)

unset MYAPP_DB_HOST && python myapp.py
# Result: result.db.host = "rc-host" (RC file, no CLI or ENV)
```

## Step 5: Add Validation

Enhance your spec with validation rules:

```yaml
parameters:
  - namespace: db
    name: host
    type: string
    required: true      # Must be provided

  - namespace: db
    name: port
    type: number
    default: 5432
    min: 1              # Minimum value
    max: 65535          # Maximum value

  - namespace: null
    name: environment
    type: string
    default: development
    accepts:            # Only these values allowed
      - development
      - staging
      - production
```

Invalid values raise clear errors:

```bash
python myapp.py --db.port 99999
# Error: Parameter 'port' value 99999 exceeds maximum 65535

python myapp.py --environment invalid
# Error: Parameter 'environment' value 'invalid' not in accepted values
```

## Next Steps

- **[Build a CLI App](cli-app.md)** — Add commands and subcommands
- **[Validate Inputs](../how-to/validate-inputs.md)** — Advanced validation rules
- **[Handle Secrets](../how-to/handle-secrets.md)** — Encrypt sensitive values
- **[YAML Schema Reference](../reference/yaml-schema.md)** — All configuration options
