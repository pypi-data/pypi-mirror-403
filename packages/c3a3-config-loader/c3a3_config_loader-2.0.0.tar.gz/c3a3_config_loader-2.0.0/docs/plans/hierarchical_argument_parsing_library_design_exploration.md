# Hierarchical Command System for config_loader v2.0

## 1. Motivation

Most existing Python argument-parsing libraries (e.g. `argparse`, `click`, `typer`) model commands as *flat* or *shallow* trees and focus primarily on **parsing** rather than **reasoning about command structure**.

This library explores a different core idea:

> A command line is a **path through a tree**, and arguments become *contextual capabilities* that appear, disappear, or change meaning as you traverse that tree.

The design aims to support:
- Deeply nested sub-commands
- Context-sensitive arguments
- Argument inheritance and scoping
- Order-sensitive or order-insensitive parsing (configurable)
- Interactive and programmatic traversal of the command tree (for CLIs, UIs, REPLs, autocompletion, etc.)

---

## 2. Core Concepts

### 2.1 Command Tree

The command structure is represented as a **directed tree**:

- Each node represents a *command context*
- Each edge represents a *sub-command transition*
- Traversing the tree builds execution context

Example:

```
exec
 └── deploy
     ├── staging
     │    ├── preview
     │    └── full
     └── production
          └── canary
```

A command line such as:

```
exec deploy staging preview
```

Is interpreted as:

```
root → deploy → staging → preview
```

> **Note:** Command names MUST NOT contain dots. Dots are reserved for parameter namespacing (see §13).

---

### 2.2 Terminal vs Non-Terminal Commands

Each command node declares whether it is:

- **Terminal** – a valid executable command
- **Non-terminal** – only a namespace / grouping

This allows constructs like:

- `exec deploy` → valid (terminal)
- `exec deploy staging` → valid (terminal)
- `exec deploy staging preview` → valid (terminal)
- `exec config` → invalid (non-terminal, only a grouping)

---

## 3. Arguments

### 3.1 Argument Definition

Arguments are first-class objects with the following properties:

- **Names**
  - Long: `--arg-name`
  - Short: `-a`
- **Kind**
  - Flag (boolean)
  - Value (single)
  - Multi-value (repeatable)
- **Value Syntax**
  - `--arg value`
  - `-a value`
  - `--arg=value`
- **Type System**
  - Primitive: `int`, `float`, `str`, `bool`
  - Enum
  - Callable validator
  - Dynamic provider (lazy fetch)

---

### 3.2 Argument Scope & Lifetime

Arguments are associated with **command nodes** and have explicit *visibility rules*.

#### Scope Types

| Scope | Description |
|-----|------------|
| `local` | Valid only if the command ends exactly at this node |
| `inherited` | Becomes available to all descendant commands |
| `ephemeral` | Valid only while parsing this node (used for modifiers) |

Example:

- `deploy` defines `--region (inherited)`
- `staging` defines `--preview-url (local)`

Valid:
```
exec deploy staging --region us-east-1 --preview-url https://...
```

Invalid:
```
exec deploy production --preview-url https://...
```
(because `--preview-url` is local to `staging`, not available in `production`)

---

### 3.3 Argument Ordering Rules

Argument placement is configurable per command node:

| Mode | Meaning |
|----|--------|
| `strict` | Arguments must appear *after* their command |
| `relaxed` | Arguments may appear before or after |
| `interleaved` | Arguments may appear anywhere |

Example:

```
exec deploy --region us-east-1 staging   # allowed or rejected depending on config
```

---

## 4. Parsing Model

### 4.1 Two-Phase Parsing

The parser operates in two conceptual phases:

#### Phase 1: Structural Traversal

- Consume tokens left-to-right
- Resolve commands and sub-commands
- Build the command path
- Maintain active argument scopes

#### Phase 2: Argument Binding

- Parse argument tokens
- Validate values
- Apply inheritance rules
- Detect conflicts or missing required arguments

This separation allows:
- Early detection of invalid paths
- Interactive inspection mid-parse

---

## 5. Interactive Traversal API

A major differentiator of this library is **interactive introspection**.

### 5.1 Traversal Session

A traversal session represents *partial command state*:

```python
session = config_loader v2.start()
```

At any moment, the caller can query:

```python
session.available_commands()
session.available_arguments()
session.expected_value_for("--arg")
```

---

### 5.2 Value Providers

Arguments may define dynamic value sources:

```python
Argument(
    name="--region",
    value_provider=lambda ctx: fetch_regions(ctx.user)
)
```

This supports:
- Shell autocompletion
- Interactive UIs
- REPL-based command builders

---

## 6. Execution Context

After parsing, the result is an **Execution Context**:

```python
ExecutionContext(
    command_path=["deploy", "staging"],
    arguments={
        "region": "us-east-1",
        "preview_url": "https://..."
    }
)
```

The context is:
- Immutable
- Serializable
- Explicitly scoped

---

## 7. Error Model

Errors are structural, not textual:

- Unknown command
- Invalid argument for this context
- Missing required argument
- Invalid value
- Ordering violation

Each error contains:
- Location in token stream
- Expected alternatives
- Human-readable message

This enables high-quality UX and editor tooling.

---

## 8. Comparison to Existing Libraries

| Feature | argparse | click | typer | config_loader v2 |
|------|---------|------|-------|--------|
| Deep command tree | ⚠️ | ✅ | ✅ | ✅ |
| Argument inheritance | ❌ | ⚠️ | ⚠️ | ✅ |
| Order sensitivity config | ❌ | ❌ | ❌ | ✅ |
| Interactive introspection | ❌ | ❌ | ❌ | ✅ |
| Dynamic value providers | ❌ | ⚠️ | ⚠️ | ✅ |

---

## 9. Non-Goals

- Shell rendering (left to integration)
- Opinionated UX output
- Execution dispatch (library focuses on parsing & context)

---

## 10. Open Design Questions

- ~~Should commands be single tokens or token groups?~~ **Resolved:** Single tokens only. No dots allowed in command names.
- ~~How to model mutually exclusive argument groups?~~ **Resolved:** See §23 (Mutually Exclusive Groups).
- ~~Should argument precedence be configurable?~~ **Resolved:** Command arguments are args-only. Parameters retain their precedence model.
- ~~Should command nodes support aliases?~~ **Resolved:** Yes, see §22 (Command Aliases).

---

## 11. Suggested Next Steps

### Phase 1: Core Infrastructure
1. Update JSON schema to version 2.0 with new fields (§18)
2. Review existing tests for v2.0 compatibility (§21.1)
3. Implement command tree data structures and validation
4. Implement token classification rules (§34)

### Phase 2: Parsing
5. Implement three-phase parsing model (§16)
6. Add command parsing tests (§21.2.1 - §21.2.4)
7. Implement argument scoping (local, inherited, ephemeral)

### Phase 3: Extended Features
8. Implement command aliases (§22)
9. Implement mutually exclusive groups (§23)
10. Implement environment variables for command args (§24)
11. Implement argument precedence across scopes (§25)
12. Implement variadic positional arguments (§27)

### Phase 4: Validation & Errors
13. Implement value provider protocol (§26)
14. Implement inter-argument dependencies/validators (§33)
15. Implement error recovery and suggestions (§28)
16. Add integration tests (§21.2.5 - §21.2.8)

### Phase 5: Result & Output
17. Update `ConfigurationResult` → `ProcessingResult` with `CommandContext` (§17)
18. Implement serialization format (§31)
19. Implement default values with variable expansion (§29)
20. Implement deprecation model (§30)

### Phase 6: User Experience
21. Implement context-sensitive help system (§20)
22. Implement short flag collision rules (§32)
23. Add help, error message, and deprecation tests (§21.2.9 - §21.2.10, §35)

### Phase 7: Finalization
24. Run full backward compatibility test suite (§21.2.11)
25. Prototype interactive session API (§5)
26. Build reference CLI using the library
27. Add shell completion adapters

---

## 12. Summary

This library extends `config_loader` to treat command lines as **structured paths with evolving capability sets**, while maintaining the existing parameters system for execution context.

**Key design decisions:**
- Parameters (context) and commands (actions) are separate concerns
- Dots reserved for parameter namespacing; commands use space-separated tokens
- Three-phase parsing: global params → command path → command args
- Reserved names (`--help`, `--version`, `--debug`) can be disabled per-spec
- Schema version 2.0 for breaking changes; 1.x specs remain compatible
- Command aliases for user convenience (§22)
- Mutually exclusive groups and inter-argument dependencies (§23, §33)
- Optional environment variable support for command arguments (§24)
- Value provider protocol with defined lifecycle (§26)
- Variadic positional arguments (§27)
- Intelligent error recovery with "did you mean?" suggestions (§28)
- Deprecation model with migration guidance (§30)
- Serializable results for logging and replay (§31)

The result is:
- Stronger correctness guarantees
- Clear separation between configuration and action
- Better tooling support
- Rich interactive experiences
- Comprehensive validation and error handling
- CI/CD-friendly with environment variable support

It is particularly well-suited for:
- Large internal tooling
- Developer platforms
- APIs exposed via CLI
- REPL-driven systems
- CI/CD pipelines

---

## 13. Integration with Parameters System

This library extends the existing `config_loader` parameters system. The two concepts serve distinct purposes:

| Concept | Purpose | Sources | Example |
|---------|---------|---------|---------|
| **Parameters** | Execution context / configuration | args, env, rc | `--db.password`, `APP_DB_PASSWORD` |
| **Commands** | Action selection / routing | args only | `deploy staging` |
| **Command Arguments** | Command-specific options | args only | `--region us-east-1` |

### 13.1 Design Principle: Separation of Concerns

Parameters represent **what context** the application runs in (database credentials, feature flags, timeouts).

Commands represent **what action** the application performs (deploy, migrate, rollback).

These are orthogonal:

```bash
# Same command, different contexts
app --db.host=prod-db deploy staging
app --db.host=dev-db deploy staging

# Same context, different commands
app --db.host=prod-db deploy staging
app --db.host=prod-db rollback staging
```

### 13.2 Backward Compatibility

When no `commands` key is present in the spec, the system behaves exactly as schema version 1.x:
- Parameters are parsed via `--namespace.name` or `--name`
- Positional `arguments` are consumed in order
- No command tree traversal occurs

---

## 14. Namespace Separation and Naming Rules

### 14.1 Dot Notation Reserved for Parameters

**Rule:** Command names MUST NOT contain dots (`.`). Dots are exclusively reserved for parameter namespacing.

| Valid | Invalid | Reason |
|-------|---------|--------|
| `deploy` | `deploy.staging` | Dots reserved for parameters |
| `db-migrate` | `db.migrate` | Use hyphens, not dots |
| `run_tests` | `run.tests` | Use underscores, not dots |

This eliminates ambiguity:
- `--db.password` → always a parameter (namespace=`db`, name=`password`)
- `deploy staging` → always a command path

### 14.2 Command Argument Naming

**Rule:** Command argument names MUST NOT match the pattern `{namespace}.{name}` where `{namespace}` is a declared parameter namespace.

Validation occurs at spec load time:

```python
# Spec validation will REJECT this:
{
    "parameters": [
        {"namespace": "db", "name": "host", ...}
    ],
    "commands": [{
        "name": "deploy",
        "arguments": [
            {"name": "db.host", ...}  # ERROR: conflicts with parameter namespace
        ]
    }]
}
```

### 14.3 Positional Arguments

**Rule:** Positional arguments (from `arguments` in spec) are only valid at terminal command nodes.

```bash
app deploy staging input.yaml    # "input.yaml" is positional, only if "staging" is terminal
app deploy input.yaml staging    # INVALID: positional before command resolution complete
```

---

## 15. Reserved Names

### 15.1 Reserved Argument Names

The following argument names are reserved by the system:

| Name | Purpose | Disableable |
|------|---------|-------------|
| `--help`, `-h` | Display context-sensitive help | Yes |
| `--version`, `-V` | Display version information | Yes |
| `--debug` | Enable debug output | Yes |

### 15.2 Disabling Reserved Names

Reserved names can be disabled in the spec to allow user-defined behavior:

```json
{
    "schema_version": "2.0",
    "reserved": {
        "help": false,
        "version": false,
        "debug": true
    }
}
```

When disabled:
- The system will not automatically handle that argument
- User may define a parameter or command argument with that name
- User is responsible for implementing the behavior

When enabled (default):
- The name cannot be used for parameters or command arguments
- Spec validation will reject conflicts
- System provides built-in behavior

### 15.3 Reserved Command Names

No command names are reserved. However, commands named `help` or `version` will shadow the reserved arguments when at the command position:

```bash
app help          # Could be command "help" OR --help depending on spec
app --help        # Always the reserved help flag (if enabled)
```

**Recommendation:** Avoid commands named `help`, `version`, or `debug` to prevent user confusion.

---

## 16. Three-Phase Parsing Model

To integrate parameters with hierarchical commands, parsing occurs in three phases:

### Phase 1: Global Parameter Extraction

Extract parameters that are defined globally (not scoped to any command):

```bash
app --db.host=localhost deploy staging --region us-east-1
    ^^^^^^^^^^^^^^^^^^^
    Phase 1: Extract global parameter
```

Global parameters may appear anywhere in the token stream (relaxed ordering).

### Phase 2: Command Path Resolution

Consume tokens to build the command path:

```bash
app --db.host=localhost deploy staging --region us-east-1
                        ^^^^^^ ^^^^^^^
                        Phase 2: Resolve command path
```

This phase:
- Identifies command tokens vs argument tokens
- Builds `command_path = ["deploy", "staging"]`
- Determines which command arguments are in scope (inherited + local)

### Phase 3: Command Argument Binding

Bind remaining arguments according to the resolved command's scope:

```bash
app --db.host=localhost deploy staging --region us-east-1
                                       ^^^^^^^^^^^^^^^^^^
                                       Phase 3: Bind command argument
```

This phase:
- Parses command-specific arguments
- Validates required arguments
- Applies ordering rules (strict/relaxed/interleaved per command)

### 16.1 Order Sensitivity

| Token Type | Ordering |
|------------|----------|
| Global parameters | Always relaxed (may appear anywhere) |
| Commands | Always strict (must appear in path order) |
| Command arguments | Configurable per command node |

Example with `strict` command arguments:

```bash
app --db.host=x deploy --region y staging    # INVALID: --region before staging
app --db.host=x deploy staging --region y    # VALID
app deploy --db.host=x staging --region y    # VALID (global param can be anywhere)
```

---

## 17. Unified Result Structure

The parsing result combines parameters and command context:

```python
@dataclass
class ProcessingResult:
    """Complete result of configuration and command processing."""

    # Parameters (from args/env/rc with precedence)
    config: ConfigurationResult  # existing structure

    # Command execution context (from args only)
    command: Optional[CommandContext]

@dataclass
class CommandContext:
    """Result of command path resolution."""

    # The resolved command path
    path: List[str]  # e.g., ["deploy", "staging"]

    # Command arguments (scoped to this path)
    arguments: Dict[str, Any]  # e.g., {"region": "us-east-1"}

    # Whether the command is terminal
    terminal: bool
```

### 17.1 Access Patterns

```python
result = cfg.process(sys.argv[1:])

# Access parameters (unchanged from v1.x)
result.config.db.host          # "localhost"
result.config.db.password      # "obfuscated:..."

# Access command context (new in v2.0)
result.command.path            # ["deploy", "staging"]
result.command.arguments       # {"region": "us-east-1"}
result.command.terminal        # True

# Check if commands were used
if result.command:
    dispatch(result.command.path, result.command.arguments)
```

### 17.2 Debug Output

With `--debug`, output shows both parameters and command context:

```
Configuration Sources:
  db.host: args
  db.password: env

Command Path: deploy → staging
Command Arguments:
  region: us-east-1 (from args)
```

---

## 18. Schema Version 2.0

This integration constitutes a breaking change. Schema version `2.0` is required.

### 18.1 Schema Changes

```json
{
    "schema_version": "2.0",
    "app_name": "myapp",

    "reserved": {
        "help": true,
        "version": true,
        "debug": true
    },

    "precedence": ["args", "env", "rc"],

    "parameters": [
        {"namespace": "db", "name": "host", "type": "string", "required": true}
    ],

    "arguments": [
        {"name": "config_file", "type": "string", "required": false}
    ],

    "commands": [
        {
            "name": "deploy",
            "terminal": true,
            "arguments": [
                {"name": "region", "type": "string", "scope": "inherited"}
            ],
            "subcommands": [
                {
                    "name": "staging",
                    "terminal": true,
                    "arguments": [
                        {"name": "preview-url", "type": "string", "scope": "local"}
                    ]
                },
                {
                    "name": "production",
                    "terminal": true,
                    "ordering": "strict"
                }
            ]
        }
    ]
}
```

### 18.2 New Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `reserved` | object | all true | Enable/disable reserved argument names |
| `commands` | array | `[]` | Command tree definition |
| `commands[].name` | string | required | Command name (no dots) |
| `commands[].terminal` | boolean | `false` | Whether this node is executable |
| `commands[].ordering` | string | `"relaxed"` | Argument ordering: `strict`, `relaxed`, `interleaved` |
| `commands[].arguments` | array | `[]` | Command-specific arguments |
| `commands[].arguments[].scope` | string | `"local"` | Visibility: `local`, `inherited`, `ephemeral` |
| `commands[].subcommands` | array | `[]` | Child command nodes |

### 18.3 Migration from 1.x

1. Update `schema_version` to `"2.0"`
2. Existing `parameters` and `arguments` continue to work unchanged
3. Add `commands` array if hierarchical commands are needed
4. Review parameter namespace names to ensure no conflicts with planned command argument names

---

## 19. Validation Rules Summary

The following validations occur at spec load time:

| Rule | Error |
|------|-------|
| Command name contains `.` | `InvalidCommandName: dots reserved for parameters` |
| Command argument matches `{ns}.{name}` | `NameConflict: argument shadows parameter namespace` |
| Reserved name used when enabled | `ReservedName: --help is reserved (disable in spec to override)` |
| Positional argument in non-terminal command | `InvalidPositional: positional args only at terminal nodes` |
| Duplicate command name at same level | `DuplicateCommand: "deploy" already defined` |
| Duplicate argument name in scope | `DuplicateArgument: "--region" already in scope via inheritance` |

---

## 20. Help System

### 20.1 Context-Sensitive Help

Help output adapts to the command path:

```bash
app --help                    # Show global params + root commands
app deploy --help             # Show deploy's args + subcommands + inherited params
app deploy staging --help     # Show staging's args + inherited from deploy + global params
```

### 20.2 Help Output Structure

```
Usage: myapp [OPTIONS] <COMMAND> [ARGS]

Global Options:
  --db.host <HOST>          Database hostname [required]
  --db.password <PASS>      Database password [obfuscated]
  --debug                   Show debug information

Commands:
  deploy      Deploy the application
  migrate     Run database migrations
  rollback    Rollback to previous version

Run 'myapp <command> --help' for command-specific options.
```

For `app deploy --help`:

```
Usage: myapp deploy [OPTIONS] <SUBCOMMAND>

Options (inherited by subcommands):
  --region <REGION>         Deployment region

Subcommands:
  staging      Deploy to staging environment
  production   Deploy to production environment

Global Options:
  --db.host <HOST>          Database hostname [required]
  --debug                   Show debug information
```

---

## 21. Testing Requirements

### 21.1 Existing Tests to Review

The following existing test areas must be reviewed for compatibility with v2.0:

| Test Area | File | Review Focus |
|-----------|------|--------------|
| Parameter parsing | `test_config_loader.py` | Ensure parameters work unchanged when no commands defined |
| Positional arguments | `test_config_loader.py` | Verify interaction with command parsing |
| Precedence handling | `test_config_loader.py` | Confirm args > env > rc still applies to parameters |
| Debug output | `test_config_loader.py` | Update expected output format for new structure |
| Auto-loading | `test_config_file_loading.py` | Add schema version 2.0 test files |
| Schema validation | `test_config_file_loading.py` | Validate new fields are accepted |

### 21.2 New Test Categories

#### 21.2.1 Command Tree Parsing

```python
# Basic command resolution
def test_single_command():
    """app deploy → command_path=["deploy"]"""

def test_nested_commands():
    """app deploy staging → command_path=["deploy", "staging"]"""

def test_deeply_nested_commands():
    """app deploy staging preview → command_path=["deploy", "staging", "preview"]"""

def test_unknown_command_error():
    """app unknown → raises UnknownCommandError"""

def test_non_terminal_command_error():
    """app config (non-terminal) → raises NonTerminalCommandError"""
```

#### 21.2.2 Namespace Separation

```python
# Dot notation reserved for parameters
def test_parameter_with_namespace():
    """--db.host=x parses as parameter, not command"""

def test_command_without_dots():
    """deploy staging parses as command path"""

def test_command_name_with_dot_rejected():
    """Spec with command name "deploy.staging" raises InvalidCommandName"""

def test_command_arg_shadowing_param_rejected():
    """Command arg "--db.host" with param namespace "db" raises NameConflict"""
```

#### 21.2.3 Three-Phase Parsing

```python
# Phase 1: Global parameters anywhere
def test_global_param_before_command():
    """--db.host=x deploy staging → param extracted, command resolved"""

def test_global_param_after_command():
    """deploy staging --db.host=x → param extracted, command resolved"""

def test_global_param_between_commands():
    """deploy --db.host=x staging → param extracted, command resolved"""

# Phase 2: Command path resolution
def test_command_path_order_matters():
    """deploy staging ≠ staging deploy"""

# Phase 3: Command argument binding
def test_command_arg_binding():
    """deploy staging --region=us-east-1 → arguments={"region": "us-east-1"}"""

def test_inherited_arg_available_in_subcommand():
    """deploy --region=x staging → region available in staging"""

def test_local_arg_not_available_in_sibling():
    """staging defines --preview-url; production --preview-url=x → error"""
```

#### 21.2.4 Argument Scope

```python
def test_local_scope_at_terminal():
    """Local arg available when command ends at defining node"""

def test_local_scope_not_inherited():
    """Local arg not available in child commands"""

def test_inherited_scope_in_children():
    """Inherited arg available in all descendant commands"""

def test_ephemeral_scope_only_during_parse():
    """Ephemeral arg valid only while parsing that node"""
```

#### 21.2.5 Ordering Rules

```python
def test_strict_ordering_enforced():
    """With ordering=strict, --arg before subcommand → error"""

def test_relaxed_ordering_allowed():
    """With ordering=relaxed, --arg before subcommand → ok"""

def test_interleaved_ordering():
    """With ordering=interleaved, args anywhere → ok"""

def test_global_params_always_relaxed():
    """Parameters can appear anywhere regardless of command ordering"""
```

#### 21.2.6 Reserved Names

```python
def test_help_reserved_by_default():
    """--help triggers help output, not parsed as user arg"""

def test_help_disabled_allows_user_definition():
    """reserved.help=false allows --help as user parameter"""

def test_reserved_name_in_param_rejected():
    """Parameter named "help" with reserved.help=true → error"""

def test_reserved_name_in_command_arg_rejected():
    """Command arg named "help" with reserved.help=true → error"""

def test_version_reserved_by_default():
    """--version triggers version output"""

def test_debug_reserved_by_default():
    """--debug triggers debug output"""
```

#### 21.2.7 Result Structure

```python
def test_result_has_config_and_command():
    """Result contains both config (params) and command (context)"""

def test_config_access_unchanged():
    """result.config.db.host works as in v1.x"""

def test_command_path_accessible():
    """result.command.path returns list of command names"""

def test_command_arguments_accessible():
    """result.command.arguments returns dict of command args"""

def test_command_none_when_no_commands():
    """Spec without commands → result.command is None"""

def test_terminal_flag_accessible():
    """result.command.terminal indicates if command is executable"""
```

#### 21.2.8 Schema Validation

```python
def test_schema_version_2_required_for_commands():
    """schema_version=1.0 with commands → error or warning"""

def test_schema_version_2_accepts_new_fields():
    """reserved, commands fields accepted in 2.0"""

def test_schema_version_1_still_works():
    """Existing 1.0 specs continue to work unchanged"""

def test_command_name_validation():
    """Command names validated: no dots, no reserved conflicts"""

def test_command_argument_validation():
    """Command args validated: no namespace conflicts"""
```

#### 21.2.9 Help System

```python
def test_root_help_shows_global_params():
    """--help at root shows parameters"""

def test_root_help_shows_commands():
    """--help at root shows available commands"""

def test_command_help_shows_inherited():
    """deploy --help shows inherited args from deploy"""

def test_command_help_shows_subcommands():
    """deploy --help shows staging, production"""

def test_subcommand_help_shows_local_args():
    """deploy staging --help shows --preview-url"""

def test_help_disabled_no_output():
    """reserved.help=false → --help not handled by system"""
```

#### 21.2.10 Error Messages

```python
def test_unknown_command_error_message():
    """Error includes available commands at that level"""

def test_invalid_arg_error_message():
    """Error includes valid args for current scope"""

def test_missing_required_arg_error_message():
    """Error specifies which required arg is missing"""

def test_ordering_violation_error_message():
    """Error explains ordering rule that was violated"""

def test_name_conflict_error_at_load():
    """Spec load error clearly identifies conflicting names"""
```

#### 21.2.11 Backward Compatibility

```python
def test_v1_spec_no_commands_works():
    """Existing v1.x spec without commands works identically"""

def test_v1_parameters_unchanged():
    """Parameters behave same as v1.x"""

def test_v1_arguments_unchanged():
    """Positional arguments behave same as v1.x"""

def test_v1_precedence_unchanged():
    """Precedence rules unchanged for parameters"""

def test_v2_without_commands_same_as_v1():
    """v2.0 spec without commands key behaves like v1.x"""
```

#### 21.2.12 Edge Cases

```python
def test_empty_command_tree():
    """commands=[] behaves like no commands"""

def test_single_terminal_root_command():
    """Single command at root level works"""

def test_command_with_no_arguments():
    """Command node with no arguments defined"""

def test_deeply_nested_inheritance():
    """Inherited arg available 5+ levels deep"""

def test_multiple_inherited_same_name():
    """Child redefines inherited arg → uses child's definition"""

def test_positional_after_command_args():
    """app deploy staging --region=x input.yaml → positional parsed"""

def test_command_arg_looks_like_command():
    """--staging (arg) vs staging (command) disambiguation"""
```

### 21.3 Test Coverage Requirements

| Area | Minimum Coverage |
|------|------------------|
| Command tree parsing | 95% |
| Three-phase parsing | 95% |
| Argument scoping | 90% |
| Reserved names | 100% |
| Schema validation | 100% |
| Backward compatibility | 100% |
| Error messages | 80% |
| Command aliases | 95% |
| Exclusion groups | 95% |
| Env vars for command args | 90% |
| Value providers | 90% |
| Validators | 90% |
| Deprecation | 90% |
| Serialization | 95% |

### 21.4 Test File Organization

```
tests/
├── test_config_loader.py          # Existing v1.x tests (review for compatibility)
├── test_config_file_loading.py    # Existing auto-load tests (add v2.0 cases)
├── test_commands.py               # NEW: Command tree parsing
├── test_command_arguments.py      # NEW: Command argument scoping & binding
├── test_three_phase_parsing.py    # NEW: Integration of params + commands
├── test_reserved_names.py         # NEW: Reserved name handling
├── test_help_system.py            # NEW: Context-sensitive help
├── test_backward_compatibility.py # NEW: v1.x spec compatibility
├── test_aliases.py                # NEW: Command alias resolution
├── test_exclusion_groups.py       # NEW: Mutually exclusive arguments
├── test_env_command_args.py       # NEW: Env vars for command arguments
├── test_value_providers.py        # NEW: Dynamic value provider protocol
├── test_validators.py             # NEW: Inter-argument dependencies
├── test_deprecation.py            # NEW: Deprecation warnings
└── fixtures/
    ├── v1_specs/                  # Existing v1.x test specs
    └── v2_specs/                  # NEW: v2.0 test specs with commands
```

---

## 22. Command Aliases

Commands may define aliases for convenience and discoverability.

### 22.1 Schema Definition

```json
{
    "commands": [
        {
            "name": "remove",
            "aliases": ["rm", "delete"],
            "terminal": true
        },
        {
            "name": "list",
            "aliases": ["ls"],
            "terminal": true
        }
    ]
}
```

### 22.2 Resolution Rules

1. During Phase 2 (Command Path Resolution), aliases are checked **after** primary names
2. If a token matches both a primary name and an alias of a sibling, primary name wins
3. Aliases must be unique within the same command level (no two siblings can share an alias)
4. Aliases cannot contain dots (same rule as command names)
5. Aliases appear in help output with indication: `rm, delete (aliases for: remove)`

### 22.3 Validation

```python
# Spec validation will REJECT:
{
    "commands": [
        {"name": "remove", "aliases": ["rm"]},
        {"name": "reset", "aliases": ["rm"]}  # ERROR: duplicate alias "rm"
    ]
}
```

---

## 23. Mutually Exclusive Groups

Arguments within a command can be grouped into mutually exclusive sets.

### 23.1 Schema Definition

```json
{
    "commands": [{
        "name": "auth",
        "terminal": true,
        "arguments": [
            {"name": "token", "type": "string"},
            {"name": "username", "type": "string"},
            {"name": "password", "type": "string"}
        ],
        "exclusion_groups": [
            {
                "name": "credentials",
                "arguments": ["token", "username"],
                "required": true,
                "message": "Provide either --token OR --username/--password"
            }
        ]
    }]
}
```

### 23.2 Semantics

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Identifier for error messages |
| `arguments` | array | Argument names that are mutually exclusive |
| `required` | boolean | If true, at least one must be provided |
| `message` | string | Custom error message (optional) |

### 23.3 Behavior

- If multiple arguments from the same exclusion group are provided → error
- If `required: true` and none provided → error
- Exclusion groups are validated in Phase 3 (Argument Binding)
- Groups can reference inherited arguments

### 23.4 Complex Example: Co-Dependent Arguments

For cases where arguments must appear together (e.g., `--username` requires `--password`):

```json
{
    "exclusion_groups": [
        {
            "name": "auth_method",
            "arguments": ["token", "username"],
            "required": true
        }
    ],
    "dependency_rules": [
        {
            "if": "username",
            "then_require": ["password"],
            "message": "--username requires --password"
        }
    ]
}
```

---

## 24. Environment Variables for Command Arguments

Command arguments can optionally be populated from environment variables.

### 24.1 Schema Definition

```json
{
    "commands": [{
        "name": "deploy",
        "arguments": [
            {
                "name": "region",
                "type": "string",
                "env": true,
                "env_name": "DEPLOY_REGION"
            }
        ]
    }]
}
```

### 24.2 Environment Variable Naming

| Field | Behavior |
|-------|----------|
| `env: false` (default) | No environment variable support |
| `env: true` | Auto-generate name: `{APP}_{COMMAND_PATH}_{ARG}` |
| `env_name: "CUSTOM"` | Use explicit name (implies `env: true`) |

Auto-generated example for `myapp deploy staging --region`:
```
MYAPP_DEPLOY_STAGING_REGION=us-east-1
```

### 24.3 Precedence

When `env: true`, command arguments follow this precedence:

1. **Command line** (highest) - explicit `--region us-east-1`
2. **Environment variable** - `MYAPP_DEPLOY_REGION=us-east-1`
3. **Default value** (lowest) - from spec

Note: RC files do NOT apply to command arguments (commands are inherently interactive).

### 24.4 Scope Inheritance

For inherited arguments with `env: true`, the environment variable name uses the **defining command's path**, not the executing command's path:

```json
{
    "name": "deploy",
    "arguments": [{"name": "region", "env": true, "scope": "inherited"}]
}
```

Both `deploy staging` and `deploy production` read from `MYAPP_DEPLOY_REGION`.

---

## 25. Argument Precedence Across Scopes

When the same argument name exists at multiple levels in the command tree, explicit rules determine which definition applies.

### 25.1 Redefinition Rules

| Scenario | Behavior |
|----------|----------|
| Child redefines inherited arg | Child's definition takes precedence |
| Same arg in two inherited ancestors | Nearest ancestor wins |
| Arg value provided at multiple levels | Last (deepest) value wins |

### 25.2 Example

```bash
# deploy defines --region (inherited), staging redefines --region (local)
app deploy --region=us-west staging --region=us-east

# Result: region = "us-east" (staging's local value wins)
```

### 25.3 Explicit Override Syntax (Optional)

For disambiguation, users can qualify the argument with the command path:

```bash
app deploy staging --deploy:region=us-west --staging:region=us-east
```

This is opt-in via spec:
```json
{
    "allow_qualified_args": true
}
```

### 25.4 Conflict Detection

At spec load time, warn (not error) if:
- A child argument shadows a parent's inherited argument with different semantics (type, required, etc.)
- This may indicate unintentional shadowing

---

## 26. Value Provider Protocol

Dynamic value providers must implement a defined protocol with clear lifecycle semantics.

### 26.1 Protocol Definition

```python
from typing import Protocol, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ProviderContext:
    """Context available to value providers."""
    command_path: List[str]          # Current command path
    parsed_args: Dict[str, Any]      # Arguments parsed so far
    environment: Dict[str, str]      # Environment variables
    partial_value: Optional[str]     # For autocompletion: partial input

class ValueProvider(Protocol):
    """Protocol for dynamic value providers."""

    def get_values(self, ctx: ProviderContext) -> List[str]:
        """Return list of valid values for autocompletion."""
        ...

    def validate(self, value: str, ctx: ProviderContext) -> bool:
        """Return True if value is valid."""
        ...

    @property
    def cacheable(self) -> bool:
        """If True, results may be cached for the session."""
        ...

    @property
    def async_safe(self) -> bool:
        """If True, may be called in async context."""
        ...
```

### 26.2 Lifecycle

| Phase | Provider Method Called |
|-------|------------------------|
| Autocompletion | `get_values(ctx)` with `partial_value` set |
| Help generation | `get_values(ctx)` (may be truncated in output) |
| Parsing | `validate(value, ctx)` |
| Error recovery | `get_values(ctx)` for "did you mean?" suggestions |

### 26.3 Error Handling

```python
class ValueProviderError(Exception):
    """Raised when a value provider fails."""
    pass

# If get_values() raises:
# - During autocompletion: silently return empty list
# - During help: show "(dynamic)" placeholder
# - During validation: propagate error with context
```

### 26.4 Performance Considerations

- Providers with `cacheable=True` are called once per session
- For autocompletion, providers should return within 100ms
- Large result sets (>1000 items) should implement filtering via `partial_value`

---

## 27. Variadic Positional Arguments

Positional arguments can accept multiple values.

### 27.1 Schema Definition

```json
{
    "arguments": [
        {"name": "source", "type": "string", "nargs": "+", "required": true},
        {"name": "destination", "type": "string", "required": true}
    ]
}
```

### 27.2 Nargs Values

| Value | Meaning | Example |
|-------|---------|---------|
| `1` (default) | Exactly one value | `app file.txt` |
| `"?"` | Zero or one | `app [file.txt]` |
| `"*"` | Zero or more | `app file1.txt file2.txt ...` |
| `"+"` | One or more | `app file1.txt file2.txt ...` (at least one) |
| `N` (integer) | Exactly N | `app f1.txt f2.txt f3.txt` |

### 27.3 Parsing Rules

1. Variadic arguments consume tokens until:
   - A token starting with `-` (flag/option)
   - A known command name
   - End of input
2. Only the **last** positional argument may be variadic with `"*"` or `"+"`
3. At most one `"?"` positional is allowed

### 27.4 Result Structure

```python
# For: app deploy staging file1.txt file2.txt --region us-east
result.command.positional  # ["file1.txt", "file2.txt"]
```

---

## 28. Error Recovery and Suggestions

The parser provides intelligent error messages using fuzzy matching.

### 28.1 "Did You Mean?" Algorithm

When an unknown command or argument is encountered:

1. Collect valid alternatives from current scope
2. Compute Levenshtein distance to each alternative
3. Suggest alternatives with distance ≤ 2 (configurable)
4. Sort by distance (closest first)

### 28.2 Error Message Format

```
Error: Unknown command 'statging'

Did you mean?
  staging    (distance: 1)
  stashing   (distance: 2)

Available commands at this level:
  staging, production, canary
```

### 28.3 Configuration

```json
{
    "error_recovery": {
        "suggest_distance": 2,
        "max_suggestions": 3,
        "show_available": true
    }
}
```

### 28.4 Non-Terminal Command Suggestions

When a user stops at a non-terminal command:

```
Error: 'config' is not a complete command

To continue, use one of:
  config show     Show current configuration
  config edit     Edit configuration file
  config reset    Reset to defaults
```

---

## 29. Default Values

Arguments and parameters support default values with explicit inheritance rules.

### 29.1 Schema Definition

```json
{
    "arguments": [
        {"name": "region", "type": "string", "default": "us-east-1"},
        {"name": "timeout", "type": "number", "default": 30}
    ]
}
```

### 29.2 Default Value Sources (in order)

1. **Explicit value** provided on command line
2. **Environment variable** (if `env: true`)
3. **Spec default** from argument definition
4. **Inherited default** from parent command (if `scope: inherited`)
5. **None** if no default and not required

### 29.3 Dynamic Defaults

Defaults can reference other arguments or environment:

```json
{
    "name": "output",
    "type": "string",
    "default": "${INPUT}.out",
    "default_refs": ["INPUT"]
}
```

Variable expansion occurs after all arguments are parsed.

---

## 30. Deprecation Model

Commands and arguments can be marked as deprecated with migration guidance.

### 30.1 Schema Definition

```json
{
    "commands": [{
        "name": "old-deploy",
        "deprecated": {
            "since": "2.0",
            "removed_in": "3.0",
            "replacement": "deploy",
            "message": "Use 'deploy' instead. 'old-deploy' will be removed in v3.0"
        }
    }],
    "parameters": [{
        "name": "legacy_mode",
        "deprecated": {
            "since": "2.0",
            "message": "Legacy mode is no longer supported"
        }
    }]
}
```

### 30.2 Behavior

| Field | Behavior |
|-------|----------|
| `since` | Version when deprecation started |
| `removed_in` | Version when it will be removed (optional) |
| `replacement` | Suggested alternative (optional) |
| `message` | Custom deprecation message |

### 30.3 Runtime Behavior

- Deprecated items still function normally
- A warning is emitted to stderr when used:
  ```
  DeprecationWarning: 'old-deploy' is deprecated since v2.0. Use 'deploy' instead.
  ```
- Help output shows deprecated items with `[DEPRECATED]` marker
- `--help` for deprecated command shows the deprecation message

### 30.4 Strict Mode

```json
{
    "deprecation": {
        "strict": true
    }
}
```

When `strict: true`, using deprecated items raises an error instead of warning.

---

## 31. Serialization Format

The `ProcessingResult` can be serialized for logging, debugging, and replay.

### 31.1 Supported Formats

| Format | Use Case |
|--------|----------|
| JSON | Logging, API responses |
| YAML | Human-readable debugging |
| Pickle | Python-only replay |

### 31.2 JSON Schema

```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "schema_version": {"const": "2.0"},
        "config": {
            "type": "object",
            "description": "Namespaced parameters"
        },
        "command": {
            "type": "object",
            "properties": {
                "path": {"type": "array", "items": {"type": "string"}},
                "arguments": {"type": "object"},
                "positional": {"type": "array"},
                "terminal": {"type": "boolean"}
            }
        },
        "sources": {
            "type": "object",
            "description": "Map of param/arg to source (args/env/rc/default)"
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Deprecation warnings, etc."
        }
    }
}
```

### 31.3 Non-Serializable Elements

The following are NOT included in serialization:
- Value provider functions (replaced with resolved values)
- Validator functions (validation already occurred)
- Obfuscated value keys (security)

### 31.4 Replay

```python
# Serialize
result = cfg.process(sys.argv[1:])
with open("execution.json", "w") as f:
    json.dump(result.to_dict(), f)

# Replay (for debugging)
with open("execution.json") as f:
    result = ProcessingResult.from_dict(json.load(f))
```

---

## 32. Short Flag Collision Rules

Short flags (`-v`, `-h`) require explicit precedence rules when defined at multiple scopes.

### 32.1 Precedence Order

1. **Command-local** short flag (highest priority)
2. **Inherited** short flag from nearest ancestor
3. **Global parameter** short flag (lowest priority)

### 32.2 Example

```json
{
    "parameters": [
        {"name": "verbose", "short": "v", "type": "boolean"}
    ],
    "commands": [{
        "name": "version",
        "arguments": [
            {"name": "verbose", "short": "v", "type": "boolean", "scope": "local"}
        ]
    }]
}
```

```bash
app -v              # Global verbose (no command context)
app version -v      # Command's verbose (shadows global)
app version --verbose  # Ambiguous: could be either (use long form)
```

### 32.3 Collision Detection

At spec load time:
- **Warning** if a command argument's short flag shadows a global parameter
- **Error** if two arguments at the same scope have the same short flag

### 32.4 Recommendation

Avoid short flag collisions by:
- Using unique short flags across the entire spec
- Omitting short flags for command arguments (long-form only)

---

## 33. Inter-Argument Dependencies

Complex validation rules between arguments use a validator system.

### 33.1 Schema Definition

```json
{
    "commands": [{
        "name": "deploy",
        "arguments": [
            {"name": "preview", "type": "boolean"},
            {"name": "preview-url", "type": "string"}
        ],
        "validators": [
            {
                "name": "preview_requires_url",
                "rule": "if_then",
                "if": {"arg": "preview", "eq": true},
                "then": {"require": ["preview-url"]},
                "message": "--preview requires --preview-url"
            },
            {
                "name": "custom_check",
                "rule": "callable",
                "function": "validators.check_deploy_args"
            }
        ]
    }]
}
```

### 33.2 Built-in Rules

| Rule | Description |
|------|-------------|
| `if_then` | If condition met, require/forbid other args |
| `requires` | Arg A requires arg B to be present |
| `conflicts` | Arg A conflicts with arg B |
| `callable` | Custom Python function |

### 33.3 Callable Validators

```python
# validators.py
def check_deploy_args(args: Dict[str, Any], ctx: ValidatorContext) -> Optional[str]:
    """Return None if valid, error message if invalid."""
    if args.get("output") == "json" and args.get("verbose"):
        return "--output=json is incompatible with --verbose"
    return None
```

### 33.4 Validation Order

1. Type validation (string, number, boolean)
2. Exclusion groups (§23)
3. Dependency rules (§23.4)
4. Custom validators (this section)
5. Value provider validation (§26)

---

## 34. Token Classification Rules

Clear rules for classifying input tokens as commands, arguments, or values.

### 34.1 Token Types

| Pattern | Classification |
|---------|----------------|
| `--name` | Long option |
| `--name=value` | Long option with value |
| `-x` | Short option |
| `-xyz` | Bundled short options |
| `-x value` | Short option with value |
| `--` | Options terminator |
| `command` | Command (if matches tree) |
| `value` | Positional argument |

### 34.2 Classification Algorithm

```
for each token:
    if token == "--":
        mark remaining as positional
    elif token starts with "--":
        parse as long option
    elif token starts with "-" and len > 1:
        parse as short option(s)
    elif token matches command at current level:
        advance command path
    else:
        treat as positional argument
```

### 34.3 Ambiguity Resolution

| Scenario | Resolution |
|----------|------------|
| `--region` matches both param and command arg | Command arg wins (if in command context) |
| `deploy` matches both command and positional | Command wins (try command first) |
| `-v` matches multiple short flags | Nearest scope wins (see §32) |

### 34.4 Escaping

To pass a value that looks like a command:
```bash
app deploy -- staging   # "staging" is positional, not subcommand
app --file=--weird      # "--weird" is value for --file
```

---

## 35. Additional Tests for New Features

### 35.1 Command Aliases

```python
def test_alias_resolves_to_command():
    """app rm → resolves to 'remove' command"""

def test_primary_name_wins_over_alias():
    """If 'rm' is both command and alias, command wins"""

def test_duplicate_alias_rejected():
    """Two commands with same alias → spec error"""

def test_alias_appears_in_help():
    """Help shows 'remove (aliases: rm, delete)'"""
```

### 35.2 Mutually Exclusive Groups

```python
def test_exclusion_group_error():
    """--token and --username together → error"""

def test_exclusion_group_required():
    """Neither --token nor --username → error if required"""

def test_exclusion_group_one_allowed():
    """--token alone → ok"""

def test_dependency_rule_enforced():
    """--username without --password → error"""
```

### 35.3 Environment Variables for Command Args

```python
def test_env_var_for_command_arg():
    """MYAPP_DEPLOY_REGION=x → region=x"""

def test_cli_overrides_env():
    """--region=y with MYAPP_DEPLOY_REGION=x → region=y"""

def test_custom_env_name():
    """env_name: 'CUSTOM' → reads from CUSTOM"""

def test_inherited_arg_env_uses_parent_path():
    """Inherited --region uses MYAPP_DEPLOY_REGION not MYAPP_DEPLOY_STAGING_REGION"""
```

### 35.4 Value Providers

```python
def test_value_provider_called_on_validate():
    """Provider.validate() called during parsing"""

def test_value_provider_error_propagates():
    """Provider raises → clear error message"""

def test_value_provider_caching():
    """cacheable=True → called once per session"""

def test_value_provider_autocompletion():
    """get_values() returns suggestions"""
```

### 35.5 Variadic Arguments

```python
def test_variadic_plus_requires_one():
    """nargs='+' with zero values → error"""

def test_variadic_star_allows_zero():
    """nargs='*' with zero values → ok"""

def test_variadic_stops_at_flag():
    """app f1 f2 --flag → positional=['f1', 'f2']"""

def test_only_last_positional_variadic():
    """Two variadic positionals → spec error"""
```

### 35.6 Error Recovery

```python
def test_did_you_mean_suggestion():
    """'statging' → suggests 'staging'"""

def test_non_terminal_shows_subcommands():
    """'config' alone → shows available subcommands"""

def test_max_suggestions_respected():
    """At most N suggestions shown"""
```

### 35.7 Deprecation

```python
def test_deprecated_command_warns():
    """Using deprecated command → stderr warning"""

def test_deprecated_in_help():
    """Deprecated items show [DEPRECATED]"""

def test_strict_mode_errors():
    """deprecation.strict=true → error not warning"""

def test_replacement_shown():
    """Warning includes replacement suggestion"""
```

### 35.8 Serialization

```python
def test_result_to_json():
    """ProcessingResult.to_dict() → valid JSON"""

def test_result_from_json():
    """ProcessingResult.from_dict() → equivalent result"""

def test_obfuscated_values_excluded():
    """Sensitive values not in serialized output"""

def test_sources_included():
    """Serialization includes source info for each value"""
```

### 35.9 Short Flag Collisions

```python
def test_command_short_shadows_global():
    """In command context, command's -v wins"""

def test_global_short_outside_command():
    """Without command, global -v applies"""

def test_duplicate_short_error():
    """Two args same scope same short → error"""
```

### 35.10 Inter-Argument Dependencies

```python
def test_if_then_requires():
    """--preview without --preview-url → error"""

def test_if_then_not_triggered():
    """No --preview, no --preview-url → ok"""

def test_callable_validator():
    """Custom validator function called"""

def test_validator_error_message():
    """Validator returns message → shown to user"""
```

