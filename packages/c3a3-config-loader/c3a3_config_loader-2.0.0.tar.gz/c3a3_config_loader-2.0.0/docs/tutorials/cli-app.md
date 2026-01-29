# Building a CLI App

Build a multi-command CLI application using config_loader v2.0.

## What We're Building

A deployment tool with commands like:

```bash
deploy staging --region us-east-1
deploy production --region eu-west-1 --force
rollback staging --version v1.2.3
```

## Step 1: Define the Command Structure

Create `deploy.yaml`:

```yaml
schema_version: "2.0"
app_name: deploy

commands:
  # deploy staging/production
  - name: deploy
    terminal: true
    arguments:
      - name: region
        short: r
        type: string
        required: true

      - name: force
        short: f
        type: boolean
        default: false

      - name: replicas
        type: number
        default: 3

  # rollback to previous version
  - name: rollback
    terminal: true
    arguments:
      - name: version
        short: v
        type: string
        required: true

      - name: dry-run
        type: boolean
        default: false
```

Key concepts:
- **`terminal: true`** — Command can be executed (not just a grouping)
- **`short`** — Single-letter alias (`-r` for `--region`)
- **`required`** — Must be provided
- **`default`** — Value when not specified

## Step 2: Process Commands in Python

Create `deploy.py`:

```python
#!/usr/bin/env python3
from config_loader import Configuration
import yaml
import sys

# Load spec
with open("deploy.yaml") as f:
    spec = yaml.safe_load(f)

cfg = Configuration(spec)
result = cfg.process(sys.argv[1:])

# Get command info
command = result.command.path[0]  # "deploy" or "rollback"
args = result.command.arguments

if command == "deploy":
    print(f"Deploying to region: {args['region']}")
    print(f"Replicas: {args['replicas']}")
    if args.get('force'):
        print("Force mode enabled!")
    # ... actual deployment logic

elif command == "rollback":
    print(f"Rolling back to version: {args['version']}")
    if args.get('dry-run'):
        print("(dry run - no changes will be made)")
    # ... actual rollback logic
```

Run it:

```bash
python deploy.py deploy --region us-east-1 --force
# Deploying to region: us-east-1
# Replicas: 3
# Force mode enabled!

python deploy.py rollback -v v1.2.3 --dry-run
# Rolling back to version: v1.2.3
# (dry run - no changes will be made)
```

## Step 3: Add Subcommands

Extend your spec with nested commands:

```yaml
schema_version: "2.0"
app_name: deploy

commands:
  - name: deploy
    # Not terminal - has subcommands
    subcommands:
      - name: staging
        terminal: true
        arguments:
          - name: region
            type: string
            default: us-east-1

      - name: production
        terminal: true
        arguments:
          - name: region
            type: string
            required: true

          - name: force
            type: boolean
            default: false

          - name: approval-ticket
            type: string
            required: true
```

Usage:

```bash
deploy staging
deploy staging --region eu-west-1
deploy production --region us-east-1 --force --approval-ticket PROD-123
```

In Python, the command path shows the full hierarchy:

```python
result = cfg.process(["deploy", "production", "--region", "us-east-1", ...])
print(result.command.path)  # ["deploy", "production"]
```

## Step 4: Use Inherited Arguments

Arguments can be inherited from parent commands:

```yaml
commands:
  - name: deploy
    arguments:
      # Available in ALL subcommands
      - name: verbose
        short: v
        type: boolean
        scope: inherited    # <-- Key setting
        default: false

      - name: config-file
        type: string
        scope: inherited

    subcommands:
      - name: staging
        terminal: true
        arguments:
          - name: region
            type: string

      - name: production
        terminal: true
        arguments:
          - name: region
            type: string
            required: true
```

Now `--verbose` works at any level:

```bash
deploy --verbose staging --region us-east-1
deploy staging --verbose --region us-east-1
deploy staging --region us-east-1 --verbose
```

All three produce the same result with `verbose: true`.

## Step 5: Add Validation Rules

### Exclusion Groups (Mutually Exclusive)

```yaml
- name: deploy
  terminal: true
  arguments:
    - name: quick
      type: boolean
    - name: thorough
      type: boolean

  exclusion_groups:
    - name: deploy-mode
      arguments: [quick, thorough]
      message: "Cannot use both --quick and --thorough"
```

```bash
deploy --quick --thorough
# Error: Cannot use both --quick and --thorough
```

### Dependency Rules

```yaml
- name: deploy
  terminal: true
  arguments:
    - name: notify
      type: boolean
    - name: notify-email
      type: string

  dependency_rules:
    - name: notify-needs-email
      rule: if_then
      if_arg: notify
      then_require: [notify-email]
      message: "--notify requires --notify-email"
```

```bash
deploy --notify
# Error: --notify requires --notify-email

deploy --notify --notify-email team@example.com
# OK
```

## Step 6: Add Value Providers

Provide dynamic suggestions for arguments:

```yaml
- name: deploy
  terminal: true
  arguments:
    - name: region
      type: string
      values_from: myapp.providers.get_regions
```

Create `myapp/providers.py`:

```python
def get_regions(ctx):
    """Return available AWS regions."""
    return [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
        "ap-southeast-1",
    ]
```

These values are used for:
- Validation (only listed values accepted)
- Autocompletion (with builder pattern)
- Help text generation

## Step 7: Add Command Aliases

```yaml
- name: deploy
  aliases: [d, push]    # Alternative names
  terminal: true
  arguments:
    - name: region
      type: string
```

All of these work identically:

```bash
deploy --region us-east-1
d --region us-east-1
push --region us-east-1
```

## Complete Example

See [examples/pydocker.yaml](../../examples/pydocker.yaml) for a complete real-world example wrapping Docker commands.

## Next Steps

- **[Validate Inputs](../how-to/validate-inputs.md)** — All validation features
- **[Use Value Providers](../how-to/use-value-providers.md)** — Context-aware suggestions
- **[Build Commands Programmatically](../how-to/build-commands-programmatically.md)** — Builder pattern
- **[YAML Schema Reference](../reference/yaml-schema.md)** — All configuration options
