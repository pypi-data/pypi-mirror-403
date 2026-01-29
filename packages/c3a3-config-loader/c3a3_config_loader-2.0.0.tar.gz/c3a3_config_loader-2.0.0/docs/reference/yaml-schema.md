# YAML Schema Reference

Complete reference for config_loader configuration files.

---

## Schema Versions

config_loader supports two schema versions:

| Version | Features |
|---------|----------|
| **1.0** | Parameters, CLI/ENV/RC sources, validation, encryption |
| **2.0** | All v1.0 features + hierarchical commands, value providers, builder pattern |

Specify the version at the top of your spec:

```yaml
schema_version: "1.0"   # Or "2.0"
```

---

## Top-Level Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version (`"1.0"` or `"2.0"`) |
| `app_name` | string | Application name (lowercase alphanumeric, `-`, `_`) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `precedence` | array | `[args, env, rc]` | Source priority order |
| `sources` | object | all enabled | Enable/disable sources |
| `print_help_on_err` | boolean | `false` | Show help on errors |
| `handle_protocol` | boolean | `true` | Enable protocol handling |
| `parameters` | array | `[]` | v1.x parameter definitions |
| `arguments` | array | `[]` | Positional arguments |
| `commands` | array | `[]` | v2.0 command tree |
| `reserved` | object | all enabled | Reserved argument names |
| `deprecation` | object | `{}` | Deprecation settings |
| `error_recovery` | object | `{}` | Error suggestion settings |

---

## Parameters (v1.x)

Parameters define configuration values that can come from CLI arguments, environment variables, or RC files.

```yaml
parameters:
  - namespace: db
    name: host
    type: string
    required: true

  - namespace: db
    name: port
    type: number
    default: 5432
    min: 1
    max: 65535

  - namespace: null
    name: debug
    type: boolean
    default: false
```

### Parameter Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `namespace` | string/null | no | — | Grouping namespace (use `null` for top-level) |
| `name` | string | yes | — | Parameter name |
| `type` | string | yes | — | `string`, `number`, or `boolean` |
| `required` | boolean | no | `false` | Must be provided |
| `default` | any | no | — | Default value |
| `accepts` | array | no | — | Allowed values (min 2 items) |
| `min` | number | no | — | Minimum value (numbers only) |
| `max` | number | no | — | Maximum value (numbers only) |
| `obfuscated` | boolean | no | `false` | Encrypt in memory |
| `protocol` | string | no | — | Protocol for value loading |
| `deprecated` | object | no | — | Deprecation metadata |

### How Parameters Map to Sources

```yaml
# For a parameter:
namespace: db
name: host

# Becomes:
# CLI:  --db.host VALUE
# ENV:  MYAPP_DB_HOST=VALUE  (app_name uppercased)
# RC:   [db] host = VALUE
```

For `namespace: null`:

```yaml
namespace: null
name: debug

# Becomes:
# CLI:  --debug
# ENV:  MYAPP_DEBUG=VALUE
# RC:   [default] debug = VALUE
```

---

## Positional Arguments

For scripts that take positional arguments:

```yaml
arguments:
  - name: input_file
    type: string
    required: true

  - name: output_file
    type: string
    default: output.txt
```

### Argument Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Argument name |
| `type` | string | yes | — | `string`, `number`, or `boolean` |
| `required` | boolean | no | `false` | Must be provided |
| `default` | any | no | — | Default value |
| `protocol` | string | no | — | Protocol for value loading |
| `nargs` | string/int | no | — | Argument count (see below) |

### nargs Values

| Value | Meaning |
|-------|---------|
| `?` | Zero or one value |
| `*` | Zero or more values |
| `+` | One or more values |
| `N` (integer) | Exactly N values |

---

## Commands (v2.0)

Commands create hierarchical CLI structures with subcommands.

```yaml
schema_version: "2.0"
app_name: deploy

commands:
  - name: deploy
    aliases: [d]
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
            short: f
            type: boolean
```

Usage:
```bash
deploy staging --region eu-west-1
deploy production --region us-east-1 --force
d production -r us-east-1 -f   # Using aliases
```

### Command Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Command name |
| `aliases` | array | no | `[]` | Alternative names |
| `terminal` | boolean | no | `false` | Can be executed directly |
| `ordering` | string | no | `relaxed` | Argument ordering mode |
| `arguments` | array | no | `[]` | Command arguments |
| `exclusion_groups` | array | no | `[]` | Mutually exclusive groups |
| `dependency_rules` | array | no | `[]` | Inter-argument rules |
| `validators` | array | no | `[]` | Custom validators |
| `subcommands` | array | no | `[]` | Child commands |
| `deprecated` | object | no | — | Deprecation metadata |

### Terminal vs Non-Terminal

- **Terminal commands** (`terminal: true`) can be executed directly
- **Non-terminal commands** act as namespaces and require a subcommand

```yaml
commands:
  - name: deploy       # Non-terminal (has subcommands)
    subcommands:
      - name: staging  # Terminal (can be executed)
        terminal: true
```

```bash
deploy              # Error: requires subcommand
deploy staging      # OK: terminal command
```

### Ordering Modes

| Mode | Description |
|------|-------------|
| `strict` | Arguments must come after all subcommands |
| `relaxed` | Arguments can appear anywhere (default) |
| `interleaved` | Arguments can be mixed with commands |

---

## Command Arguments

Arguments are options specific to a command.

```yaml
arguments:
  - name: region
    short: r
    type: string
    required: true
    env: true
    env_name: AWS_REGION

  - name: verbose
    short: v
    type: boolean
    scope: inherited
    default: false

  - name: files
    type: string
    nargs: "+"
```

### Command Argument Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Argument name (becomes `--name`) |
| `type` | string | no | `string` | `string`, `number`, or `boolean` |
| `short` | string | no | — | Single-letter alias (becomes `-x`) |
| `scope` | string | no | `local` | Visibility scope |
| `required` | boolean | no | `false` | Must be provided |
| `default` | any | no | — | Default value |
| `env` | boolean | no | `false` | Read from environment |
| `env_name` | string | no | — | Custom env var name |
| `nargs` | string/int | no | — | Argument count |
| `values_from` | string | no | — | Value provider path |
| `deprecated` | object | no | — | Deprecation metadata |

### Argument Scopes

| Scope | Behavior |
|-------|----------|
| `local` | Only available in this command |
| `inherited` | Available in this command and all subcommands |
| `ephemeral` | Available in this command only, not persisted |

```yaml
commands:
  - name: deploy
    arguments:
      - name: verbose      # Available everywhere under deploy
        scope: inherited
        type: boolean

    subcommands:
      - name: staging
        terminal: true
        arguments:
          - name: region   # Only available in staging
            scope: local
            type: string
```

---

## Exclusion Groups

Define mutually exclusive arguments:

```yaml
- name: deploy
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
      required: false
      message: "Choose only one output format"
```

### Exclusion Group Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Group identifier |
| `arguments` | array | yes | — | Argument names (min 2) |
| `required` | boolean | no | `false` | At least one must be provided |
| `message` | string | no | — | Custom error message |

---

## Dependency Rules

Define conditional requirements between arguments:

```yaml
- name: deploy
  terminal: true
  arguments:
    - name: notify
      type: boolean
    - name: email
      type: string
    - name: slack
      type: boolean

  dependency_rules:
    - name: notify-needs-target
      rule: if_then
      if_arg: notify
      then_require: [email, slack]
      message: "--notify requires --email or --slack"
```

### Dependency Rule Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Rule identifier |
| `rule` | string | yes | — | Rule type |
| `if_arg` | string | no | — | Condition argument |
| `eq` | any | no | — | Condition value |
| `then_require` | array | no | — | Required arguments |
| `message` | string | no | — | Custom error message |

### Rule Types

| Type | Description |
|------|-------------|
| `if_then` | If `if_arg` is provided (or equals `eq`), require `then_require` |
| `requires` | Argument A requires argument B |
| `conflicts` | Argument A conflicts with argument B |

---

## Validators

Define custom validation rules:

```yaml
- name: deploy
  terminal: true
  arguments:
    - name: source
      type: string
    - name: target
      type: string
    - name: force
      type: boolean

  validators:
    - name: source-target-different
      rule: callable
      function: myapp.validators.check_source_target

    - name: force-requires-target
      rule: if_then
      if:
        arg: force
        eq: true
      then:
        require: [target]
      message: "--force requires --target"
```

### Validator Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Validator identifier |
| `rule` | string | yes | `if_then`, `requires`, `conflicts`, or `callable` |
| `if` | object | no | Condition (for if_then) |
| `then` | object | no | Action (for if_then) |
| `function` | string | no | Python function path (for callable) |
| `message` | string | no | Custom error message |

---

## Value Providers

Dynamic value suggestions for arguments:

```yaml
arguments:
  - name: region
    type: string
    values_from: myapp.providers.get_aws_regions
```

Provider function:

```python
# myapp/providers.py
def get_aws_regions(ctx):
    """Return available AWS regions."""
    return ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
```

The function receives a `ProviderContext` with:
- `command_path`: Current command hierarchy
- `parsed_args`: Already-parsed arguments
- `environment`: Environment variables
- `partial_value`: Partial value for completion

---

## Deprecation

Mark commands or arguments as deprecated:

```yaml
commands:
  - name: old-deploy
    terminal: true
    deprecated:
      since: "2.0"
      removed_in: "3.0"
      replacement: deploy
      message: "Use 'deploy' command instead"
```

### Deprecation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `since` | string | yes | Version when deprecation started |
| `removed_in` | string | no | Version when item will be removed |
| `replacement` | string | no | Suggested alternative |
| `message` | string | no | Custom deprecation message |

### Global Deprecation Settings

```yaml
deprecation:
  strict: true   # Errors instead of warnings
```

---

## Reserved Arguments

Control built-in argument names:

```yaml
reserved:
  help: true      # --help, -h (default: true)
  version: true   # --version, -V (default: true)
  debug: true     # --debug (default: true)
```

Set to `false` to use these names for your own arguments.

---

## Error Recovery

Configure error suggestions:

```yaml
error_recovery:
  suggest_distance: 2    # Max Levenshtein distance for "did you mean?"
  max_suggestions: 3     # Maximum suggestions to show
  show_available: true   # Show available commands/arguments
```

---

## Source Configuration

### Precedence

Control which source wins when values conflict:

```yaml
precedence:
  - args   # CLI arguments (checked first)
  - env    # Environment variables
  - rc     # RC file (checked last)
```

### Enable/Disable Sources

```yaml
sources:
  args: true   # Enable CLI arguments
  env: true    # Enable environment variables
  rc: false    # Disable RC file loading
```

---

## Complete Example

```yaml
schema_version: "2.0"
app_name: myapp

precedence: [args, env, rc]
sources:
  args: true
  env: true
  rc: true

reserved:
  help: true
  version: true

error_recovery:
  suggest_distance: 2
  max_suggestions: 3

# Global parameters (v1.x style)
parameters:
  - namespace: db
    name: host
    type: string
    required: true
  - namespace: db
    name: port
    type: number
    default: 5432

# Commands (v2.0)
commands:
  - name: deploy
    aliases: [d]
    arguments:
      - name: verbose
        short: v
        type: boolean
        scope: inherited
        default: false

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
            short: f
            type: boolean
          - name: approval
            type: string
            required: true

        exclusion_groups:
          - name: deploy-mode
            arguments: [quick, full]
            message: "Choose --quick or --full, not both"

        dependency_rules:
          - name: force-needs-approval
            rule: if_then
            if_arg: force
            then_require: [approval]
            message: "--force requires --approval"

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

---

## See Also

- **[Python API](python-api.md)** — Classes and methods
- **[CLI Conventions](cli-conventions.md)** — Argument syntax
- **[Architecture](../explanation/architecture.md)** — How it all fits together
