# How to Validate Inputs

Comprehensive guide to validating configuration and command arguments.

---

## Basic Validation

### Required Fields

Make a parameter required:

```yaml
parameters:
  - namespace: db
    name: host
    type: string
    required: true  # Must be provided via CLI, ENV, or RC
```

Error when missing:

```
Error: Required parameter db.host not provided
```

### Type Validation

Values are automatically parsed and validated:

```yaml
parameters:
  - namespace: db
    name: port
    type: number    # Must be numeric
```

```bash
myapp --db.port abc
# Error: Invalid number: abc
```

### Allowed Values

Restrict to specific values:

```yaml
parameters:
  - namespace: null
    name: environment
    type: string
    accepts:
      - development
      - staging
      - production
```

```bash
myapp --environment invalid
# Error: Parameter 'environment' value 'invalid' not in accepted values
```

### Numeric Ranges

Set min/max for numbers:

```yaml
parameters:
  - namespace: db
    name: port
    type: number
    min: 1
    max: 65535
```

```bash
myapp --db.port 99999
# Error: Parameter 'port' value 99999 exceeds maximum 65535
```

---

## Exclusion Groups (v2.0)

Prevent mutually exclusive arguments from being used together.

### Basic Exclusion

```yaml
commands:
  - name: export
    terminal: true
    arguments:
      - name: json
        type: boolean
      - name: yaml
        type: boolean
      - name: table
        type: boolean

    exclusion_groups:
      - name: output-format
        arguments: [json, yaml, table]
        message: "Choose only one output format"
```

```bash
myapp export --json --yaml
# Error: Choose only one output format
```

### Required Exclusion Groups

Require at least one from a group:

```yaml
exclusion_groups:
  - name: output-format
    arguments: [json, yaml, table]
    required: true    # Must pick one
    message: "You must specify an output format"
```

```bash
myapp export
# Error: You must specify an output format
```

---

## Dependency Rules (v2.0)

Define relationships between arguments.

### If-Then Dependencies

Require arguments when a condition is met:

```yaml
commands:
  - name: deploy
    terminal: true
    arguments:
      - name: notify
        type: boolean
      - name: email
        type: string

    dependency_rules:
      - name: notify-needs-email
        rule: if_then
        if_arg: notify
        then_require: [email]
        message: "--notify requires --email"
```

```bash
myapp deploy --notify
# Error: --notify requires --email

myapp deploy --notify --email team@example.com
# OK
```

### Conditional on Value

Trigger rule only when argument equals specific value:

```yaml
dependency_rules:
  - name: force-needs-approval
    rule: if_then
    if_arg: environment
    eq: production           # Only when environment=production
    then_require: [approval]
    message: "Production deployments require --approval"
```

```bash
myapp deploy --environment production
# Error: Production deployments require --approval

myapp deploy --environment staging
# OK (no approval needed)
```

### Requires Rule

Simpler syntax when you just need "A requires B":

```yaml
dependency_rules:
  - name: ssl-needs-cert
    rule: requires
    if_arg: ssl
    then_require: [ssl-cert, ssl-key]
```

### Conflicts Rule

Prevent arguments from being used together:

```yaml
dependency_rules:
  - name: no-dry-run-with-force
    rule: conflicts
    if_arg: dry-run
    then_require: [force]   # "then_require" means "conflicts with" here
    message: "--dry-run and --force cannot be used together"
```

---

## Custom Validators (v2.0)

For complex validation logic beyond built-in rules.

### Callable Validators

Reference a Python function:

```yaml
commands:
  - name: deploy
    terminal: true
    arguments:
      - name: source
        type: string
      - name: target
        type: string

    validators:
      - name: source-target-different
        rule: callable
        function: myapp.validators.check_source_target
        message: "Source and target cannot be the same"
```

Implement the validator:

```python
# myapp/validators.py
from typing import Any, Dict, Optional
from config_loader import ValidatorContext

def check_source_target(
    args: Dict[str, Any],
    ctx: ValidatorContext
) -> Optional[str]:
    """Ensure source and target are different.

    Args:
        args: The bound argument values.
        ctx: Validation context with command path, environment.

    Returns:
        None if valid, or error message string if invalid.
    """
    source = args.get("source")
    target = args.get("target")

    if source and target and source == target:
        return f"Source '{source}' cannot be the same as target"

    return None  # Validation passed
```

### Validator with Context

Access command path and environment in validators:

```python
def check_production_deploy(
    args: Dict[str, Any],
    ctx: ValidatorContext
) -> Optional[str]:
    """Require confirmation for production deployments."""
    # Check command path
    if "production" not in ctx.command_path:
        return None

    # Check environment variable for CI
    if ctx.environment.get("CI") == "true":
        if not args.get("auto-approve"):
            return "CI production deploys require --auto-approve"

    return None
```

### Declarative If-Then in Validators

Use the validators field for if-then logic:

```yaml
validators:
  - name: verbose-json-conflict
    rule: if_then
    if:
      arg: output
      eq: json
    then:
      forbid: [verbose]   # Forbid --verbose when --output=json
    message: "--verbose is not compatible with JSON output"
```

---

## Protocol Validation

Require values to use a specific protocol:

```yaml
parameters:
  - namespace: db
    name: password
    type: string
    protocol: vault        # Must be vault://...
    obfuscated: true       # Required for sensitive protocols
```

```bash
myapp --db.password "plaintext"
# Error: Parameter db.password requires protocol 'vault' but got non-protocol value

myapp --db.password "vault://secrets/db/password"
# OK
```

---

## Combining Validation Rules

All validation rules work together:

```yaml
commands:
  - name: deploy
    terminal: true
    arguments:
      - name: environment
        type: string
        required: true
        accepts: [dev, staging, production]

      - name: force
        short: f
        type: boolean

      - name: approval-ticket
        type: string

      - name: dry-run
        type: boolean

      - name: replicas
        type: number
        default: 3
        min: 1
        max: 10

    exclusion_groups:
      - name: run-mode
        arguments: [force, dry-run]
        message: "Cannot use --force with --dry-run"

    dependency_rules:
      - name: prod-needs-approval
        rule: if_then
        if_arg: environment
        eq: production
        then_require: [approval-ticket]
        message: "Production deploys require --approval-ticket"

    validators:
      - name: ticket-format
        rule: callable
        function: myapp.validators.check_ticket_format
```

---

## Error Messages

### Default Messages

config_loader generates clear error messages:

```
Error: Required parameter db.host not provided
Error: Parameter 'port' value 99999 exceeds maximum 65535
Error: Arguments --json, --yaml are mutually exclusive (group: output-format)
Error: When '--notify' is set, --email must also be provided (rule: notify-needs-email)
```

### Custom Messages

Override with the `message` field:

```yaml
exclusion_groups:
  - name: output-format
    arguments: [json, yaml]
    message: "Please choose either JSON or YAML output, not both."

dependency_rules:
  - name: force-approval
    rule: if_then
    if_arg: force
    then_require: [approval]
    message: "Using --force requires explicit --approval for safety."
```

---

## Testing Validation

Write tests for your validation rules:

```python
import pytest
from config_loader import Configuration

def test_exclusion_group():
    spec = {
        "schema_version": "2.0",
        "app_name": "test",
        "commands": [{
            "name": "export",
            "terminal": True,
            "arguments": [
                {"name": "json", "type": "boolean"},
                {"name": "yaml", "type": "boolean"},
            ],
            "exclusion_groups": [{
                "name": "output",
                "arguments": ["json", "yaml"]
            }]
        }]
    }

    cfg = Configuration(spec)

    # Should fail with both
    with pytest.raises(ValueError, match="mutually exclusive"):
        cfg.process(["export", "--json", "--yaml"])

    # Should work with one
    result = cfg.process(["export", "--json"])
    assert result.command.arguments["json"] is True


def test_dependency_rule():
    spec = {
        "schema_version": "2.0",
        "app_name": "test",
        "commands": [{
            "name": "deploy",
            "terminal": True,
            "arguments": [
                {"name": "notify", "type": "boolean"},
                {"name": "email", "type": "string"},
            ],
            "dependency_rules": [{
                "name": "notify-email",
                "rule": "if_then",
                "if_arg": "notify",
                "then_require": ["email"]
            }]
        }]
    }

    cfg = Configuration(spec)

    # Should fail without email
    with pytest.raises(ValueError, match="email"):
        cfg.process(["deploy", "--notify"])

    # Should work with email
    result = cfg.process(["deploy", "--notify", "--email", "test@example.com"])
    assert result.command.arguments["notify"] is True
```

---

## See Also

- **[YAML Schema Reference](../reference/yaml-schema.md)** — All validation options
- **[CLI Conventions](../reference/cli-conventions.md)** — Error message format
- **[Use Value Providers](use-value-providers.md)** — Dynamic value validation
