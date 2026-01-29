# Release Notes: v2.0.0

**Release Date:** January 2025

---

## Overview

v2.0.0 introduces a hierarchical command system, enabling config_loader to power sophisticated CLI applications with subcommands, while maintaining full backward compatibility with v1.x specs.

---

## Highlights

- **Hierarchical Commands** — Build complex CLIs with nested subcommands
- **Value Providers** — Dynamic argument suggestions for autocompletion
- **Builder Pattern** — Programmatic command construction for IDEs and wizards
- **Full Backward Compatibility** — v1.x specs work unchanged

---

## New Features

### Hierarchical Command System

Define commands with unlimited nesting depth:

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
            short: r
            type: string
            required: true

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

```bash
deploy staging --region us-east-1
deploy production -r eu-west-1 --force
d staging -r us-east-1  # Using alias
```

### Argument Scoping

Control argument visibility across the command tree:

| Scope | Behavior |
|-------|----------|
| `local` | Only at the defining command (default) |
| `inherited` | Available to all subcommands |
| `ephemeral` | Local and not persisted |

```yaml
arguments:
  - name: verbose
    scope: inherited  # Available everywhere under this command
```

### Value Providers

Supply dynamic values for autocompletion and validation:

```yaml
arguments:
  - name: region
    values_from: myapp.providers.get_regions
```

```python
def get_regions(ctx):
    # Context includes command_path, parsed_args, environment
    return ["us-east-1", "us-west-2", "eu-west-1"]
```

### Builder Pattern

Construct commands programmatically with suggestions at each step:

```python
builder = cfg.builder()
suggestions = builder.check_next()  # Available commands

builder = builder.add_command("deploy")
suggestions = builder.check_next()  # Available subcommands and arguments

builder = builder.add_argument("region", "us-east-1")
result = builder.build()
```

### Exclusion Groups

Define mutually exclusive arguments:

```yaml
exclusion_groups:
  - name: output-format
    arguments: [json, yaml, table]
    required: false
    message: "Choose one output format"
```

### Dependency Rules

Express inter-argument relationships:

```yaml
dependency_rules:
  - name: notify-needs-email
    rule: if_then
    if_arg: notify
    then_require: [email]
    message: "--notify requires --email"
```

Rule types: `if_then`, `requires`, `conflicts`

### Custom Validators

Reference Python functions for complex validation:

```yaml
validators:
  - name: check-source-target
    rule: callable
    function: myapp.validators.check_source_target
```

### Deprecation Support

Mark commands or arguments as deprecated:

```yaml
commands:
  - name: old-deploy
    deprecated:
      since: "2.0"
      removed_in: "3.0"
      replacement: deploy
      message: "Use 'deploy' instead"
```

Users see warnings but commands still work:
```
Warning: 'old-deploy' is deprecated since 2.0. Use 'deploy' instead.
```

Enable strict mode to treat deprecations as errors:
```yaml
deprecation:
  strict: true
```

### Error Recovery

"Did you mean?" suggestions for typos:

```
Error: Unknown command 'depoly'. Did you mean 'deploy'?
```

Configurable:
```yaml
error_recovery:
  suggest_distance: 2
  max_suggestions: 3
  show_available: true
```

### Environment Variables for Command Arguments

Command arguments can read from environment:

```yaml
arguments:
  - name: region
    env: true
    env_name: AWS_REGION  # Optional custom name
```

### Argument Ordering Modes

Control how strictly arguments must follow commands:

| Mode | Behavior |
|------|----------|
| `strict` | Arguments must appear after the command |
| `relaxed` | Arguments can appear anywhere (default) |
| `interleaved` | Arguments can be mixed with subcommands |

### Three-Phase Parsing

New parsing model separates:
1. Global parameter extraction
2. Command path resolution
3. Command argument binding

This allows global parameters (from `parameters:`) to coexist with command arguments naturally.

### Result Serialization

Export and replay execution state:

```python
from config_loader import create_replay_file, load_replay_file

create_replay_file(result, "replay.json")
restored = load_replay_file("replay.json")
```

---

## ProcessingResult

v2.0 returns `ProcessingResult` which includes both config and command context:

```python
result = cfg.process(args)

# Global parameters (v1.x style)
result.db.host          # Still works!

# Command context (v2.0)
result.command.path       # ["deploy", "staging"]
result.command.arguments  # {"region": "us-east-1"}
result.command.terminal   # True
result.warnings           # Deprecation warnings
```

---

## Backward Compatibility

**v1.x specs work unchanged.** No migration required.

```yaml
# This v1.x spec still works perfectly in v2.0
app_name: myapp
precedence: [args, env, rc]
parameters:
  - namespace: db
    name: host
    type: string
```

The `schema_version` field distinguishes versions:
- Omit or set to `"1.0"` for v1.x behavior
- Set to `"2.0"` for new features

---

## New Dependencies

None. All v2.0 features use the standard library.

---

## Breaking Changes

**None.** v2.0 is fully backward compatible.

---

## Deprecations

None in this release.

---

## Documentation

New comprehensive documentation following the Divio system:
- Tutorials: quickstart, cli-app, migration guide
- How-to guides: validation, value providers, builder, secrets, plugins
- Reference: YAML schema, Python API, CLI conventions
- Explanation: architecture, three-phase parsing, design decisions

---

## Migration Guide

See [docs/tutorials/migration-v1-to-v2.md](docs/tutorials/migration-v1-to-v2.md) for detailed upgrade instructions.

**Quick summary:**
1. Your existing specs work unchanged
2. Add `schema_version: "2.0"` to use new features
3. Add `commands:` to define hierarchical commands
4. Access command info via `result.command`

---

## Contributors

- Core implementation and documentation

---

## Full Changelog

### Added
- Hierarchical command system with subcommands
- Command aliases
- Terminal vs non-terminal commands
- Argument scoping (local, inherited, ephemeral)
- Value providers for dynamic suggestions
- Builder pattern for programmatic construction
- Exclusion groups (mutually exclusive arguments)
- Dependency rules (if_then, requires, conflicts)
- Custom callable validators
- Deprecation tracking with warnings
- Error recovery with suggestions
- Environment variable support for command arguments
- Argument ordering modes (strict, relaxed, interleaved)
- Three-phase parsing model
- ProcessingResult with command context
- Result serialization (to_dict, to_json, from_dict)
- Comprehensive documentation

### Changed
- Updated JSON schema to v2.0
- README updated with v2.0 examples

### Fixed
- None (new major version)

### Removed
- None (fully backward compatible)
