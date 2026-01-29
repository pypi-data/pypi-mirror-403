# CLI Conventions Reference

How config_loader handles command-line arguments, environment variables, and RC files.

---

## Argument Syntax

### Long Options

Parameters use `--namespace.name` format:

```bash
myapp --db.host localhost --db.port 5432
```

For parameters without a namespace (`namespace: null`):

```bash
myapp --debug --verbose
```

### Short Options (Commands Only)

Command arguments can have short flags:

```bash
myapp deploy -r us-east-1 -f    # -r for --region, -f for --force
```

Short flags can be combined for booleans:

```bash
myapp deploy -vf    # Same as -v -f
```

### Option Formats

All of these are equivalent:

```bash
--region us-east-1
--region=us-east-1
-r us-east-1
-r=us-east-1
```

### Boolean Arguments

Booleans are true when present:

```bash
myapp --debug          # debug = True
myapp --debug true     # debug = True
myapp --debug false    # debug = False
myapp --debug=yes      # debug = True
myapp --debug=no       # debug = False
```

Accepted true values: `true`, `1`, `yes`, `on`
Accepted false values: `false`, `0`, `no`, `off`

### End of Options

Use `--` to mark the end of options:

```bash
myapp deploy -- file-that-starts-with-dash.txt
```

---

## Environment Variables

### Naming Convention

Environment variables follow `APPNAME_NAMESPACE_PARAM` format:

| Parameter | Environment Variable |
|-----------|---------------------|
| `db.host` in app `myapp` | `MYAPP_DB_HOST` |
| `debug` (no namespace) | `MYAPP_DEBUG` |
| `api.timeout` in app `deploy-tool` | `DEPLOY_TOOL_API_TIMEOUT` |

Rules:
- App name uppercased
- Dashes converted to underscores
- Namespace and name joined with underscore

### Command Arguments (v2.0)

Command arguments with `env: true` use:

```
APPNAME_COMMAND_SUBCOMMAND_ARGNAME
```

Example:

```yaml
commands:
  - name: deploy
    subcommands:
      - name: staging
        terminal: true
        arguments:
          - name: region
            env: true
```

Environment variable: `MYAPP_DEPLOY_STAGING_REGION`

Or specify a custom name:

```yaml
- name: region
  env_name: AWS_DEFAULT_REGION
```

### Boolean Values

Same as CLI:

```bash
export MYAPP_DEBUG=true     # True
export MYAPP_DEBUG=1        # True
export MYAPP_DEBUG=yes      # True
export MYAPP_DEBUG=false    # False
export MYAPP_DEBUG=0        # False
```

---

## RC Files

### Location

RC files are located at `~/.appnamerc` (TOML format):

- App `myapp` → `~/.myapprc`
- App `deploy-tool` → `~/.deploy-toolrc`

### Format

```toml
# ~/.myapprc

[db]
host = "localhost"
port = 5432

[default]
debug = true
verbose = false
```

- Namespaced parameters use `[namespace]` sections
- Non-namespaced parameters go in `[default]`

### Type Handling

TOML preserves types:

```toml
[db]
port = 5432          # number
host = "localhost"   # string

[default]
debug = true         # boolean
timeout = 30.5       # float
```

---

## Precedence

### Default Order

By default: `args > env > rc`

```yaml
precedence:
  - args    # Highest priority
  - env
  - rc      # Lowest priority
```

Values from higher-priority sources override lower ones.

### Custom Precedence

Override in spec:

```yaml
# Make environment variables highest priority
precedence:
  - env
  - args
  - rc
```

### Example

```yaml
# RC file: db.host = "rc-host"
# ENV: MYAPP_DB_HOST=env-host
# CLI: --db.host cli-host

# With default precedence [args, env, rc]:
result.db.host  # "cli-host" (CLI wins)

# Without CLI argument:
result.db.host  # "env-host" (ENV wins)

# Without CLI or ENV:
result.db.host  # "rc-host" (RC file wins)
```

---

## Command Syntax (v2.0)

### Command Path

Commands form a path:

```bash
myapp deploy staging --region us-east-1
#     └──────┬──────┘ └───────┬────────┘
#     command path      arguments
```

### Argument Placement

With `ordering: relaxed` (default), arguments can appear anywhere:

```bash
# All equivalent:
myapp deploy staging --region us-east-1
myapp deploy --region us-east-1 staging
myapp --region us-east-1 deploy staging
```

With `ordering: strict`, arguments must follow commands:

```bash
# Only this works:
myapp deploy staging --region us-east-1
```

### Inherited Arguments

Arguments with `scope: inherited` are available at any level:

```bash
# --verbose defined on 'deploy' with scope: inherited
myapp deploy --verbose staging
myapp deploy staging --verbose
myapp --verbose deploy staging    # All equivalent
```

### Aliases

Commands can have aliases:

```yaml
commands:
  - name: deploy
    aliases: [d, push]
```

```bash
myapp deploy staging     # Full name
myapp d staging          # Alias
myapp push staging       # Alias
```

---

## Reserved Arguments

By default, these are reserved:

| Argument | Short | Description |
|----------|-------|-------------|
| `--help` | `-h` | Show help |
| `--version` | `-V` | Show version |
| `--debug` | — | Show debug info |

Disable in spec to use for your own purposes:

```yaml
reserved:
  help: false      # Can now use --help for something else
  version: false
  debug: false
```

---

## Variadic Arguments

### nargs Options

| Value | Meaning | Example |
|-------|---------|---------|
| `?` | Zero or one | `--config file.yaml` or just `--config` |
| `*` | Zero or more | `--files a.txt b.txt c.txt` |
| `+` | One or more | `--files a.txt b.txt` (at least one required) |
| `N` | Exactly N | `--coords 10 20` (exactly 2) |

### Usage

```yaml
arguments:
  - name: files
    type: string
    nargs: "+"
```

```bash
myapp process --files a.txt b.txt c.txt
```

Accessed as a list:

```python
result.command.arguments["files"]  # ["a.txt", "b.txt", "c.txt"]
```

---

## Protocol Values

Values can use protocol syntax for plugin-based loading:

```bash
myapp --db.password vault://secrets/db/password
myapp --api.key ssm://prod/api/key
```

Format: `protocol://value`

See [Create Plugins](../how-to/create-plugins.md) for implementing protocols.

---

## Error Messages

### Missing Required Parameter

```
Error: Required parameter db.host not provided
```

### Invalid Value

```
Error: Invalid value for db.port: not_a_number
Error: Parameter 'environment' value 'invalid' not in accepted values: [development, staging, production]
```

### Unknown Command

```
Error: Unknown command 'depoly'. Did you mean 'deploy'?
```

### Mutually Exclusive Arguments

```
Error: Cannot use both --quick and --thorough (output-format exclusion group)
```

### Missing Dependency

```
Error: --notify requires --notify-email
```

---

## See Also

- **[YAML Schema Reference](yaml-schema.md)** — All configuration options
- **[Python API Reference](python-api.md)** — Classes and methods
- **[Validate Inputs](../how-to/validate-inputs.md)** — Validation features
