# Design Decisions

Why config_loader works the way it does.

---

## Why Multi-Source Configuration?

**Problem**: Applications need configuration from multiple sources with different use cases:
- CLI for one-off overrides
- Environment variables for containers/CI
- RC files for persistent user preferences

**Decision**: Support all three sources with configurable precedence.

**Alternatives considered**:
- Single source: Too limiting for real-world use
- Hardcoded precedence: Doesn't fit all use cases

**Trade-offs**:
- (+) Flexible for any deployment model
- (+) Same spec works locally and in production
- (-) More complex than single-source
- (-) Must reason about precedence conflicts

---

## Why YAML/JSON Spec Files?

**Problem**: How should users define their configuration schema?

**Decision**: Declarative YAML/JSON files validated against a JSON Schema.

**Alternatives considered**:
- Python decorators (like Click): Less portable, harder to version
- Python classes: More boilerplate, harder to understand at a glance
- INI/TOML: Less expressive for nested structures

**Trade-offs**:
- (+) Language-agnostic specification
- (+) Easy to read and edit
- (+) Can be validated statically
- (+) Version control friendly
- (-) Separate from code (could get out of sync)
- (-) Limited expressiveness for complex validation

---

## Why Three-Phase Command Parsing?

**Problem**: How to handle both global parameters and command-specific arguments without ambiguity?

**Decision**: Three-phase parsing separates concerns:
1. Extract global parameters (can appear anywhere)
2. Resolve command path
3. Bind command arguments

**Alternatives considered**:
- Single-pass parsing: Ambiguous for `--option command` vs `command --option`
- Positional-only commands: Less flexible for users
- Separate namespaces (`--global.verbose` vs `--cmd.region`): Verbose

**Trade-offs**:
- (+) Clean separation between globals and command args
- (+) Users can place args flexibly
- (+) Clear mental model
- (-) More complex implementation
- (-) Some edge cases in ordering modes

---

## Why Argument Scoping (local/inherited/ephemeral)?

**Problem**: In hierarchical commands, which arguments should be available where?

**Decision**: Explicit scoping with three levels:
- `local`: Only at the defining command
- `inherited`: Available to all subcommands
- `ephemeral`: Local and not persisted

**Alternatives considered**:
- All arguments inherited: Pollutes subcommand namespaces
- All arguments local: Forces repetition
- Automatic inference: Unpredictable

**Trade-offs**:
- (+) Explicit control over argument visibility
- (+) Supports common patterns (verbose everywhere, region per-command)
- (+) Clear inheritance semantics
- (-) More configuration for users
- (-) Must understand scoping rules

---

## Why In-Memory Obfuscation?

**Problem**: How to prevent accidental exposure of secrets in logs, stack traces, and debug output?

**Decision**: AES-256 encryption with session-scoped keys.

**Alternatives considered**:
- Marker classes (SecretString): Easy to bypass, shows in `__repr__`
- External secret managers only: Not all environments have them
- No protection: Secrets in logs are common security issues

**Trade-offs**:
- (+) Secrets don't appear in plaintext anywhere
- (+) Works without external infrastructure
- (+) Explicit reveal() required
- (-) Performance overhead (negligible in practice)
- (-) Key exists in memory (addresses logs, not memory attacks)

---

## Why Protocol Plugins?

**Problem**: How to load values from external sources (Vault, SSM, files)?

**Decision**: Protocol-based plugin system (`vault://path`, `ssm://param`).

**Alternatives considered**:
- Built-in integrations: Bloated, opinionated dependencies
- Environment variable indirection: Doesn't solve the loading problem
- Custom loaders: No standard interface

**Trade-offs**:
- (+) Extensible without modifying core
- (+) Clear syntax in configuration
- (+) Type and constraint validation per plugin
- (-) Requires implementing plugin interface
- (-) Protocol prefix syntax is unusual

---

## Why Builder Pattern for Commands?

**Problem**: How to support IDE integrations, autocompletion, and interactive wizards?

**Decision**: Immutable builder pattern with suggestions at each step.

**Alternatives considered**:
- Mutable state machine: Harder to explore alternatives
- Direct process() call: No incremental feedback
- Callback-based: More complex API

**Trade-offs**:
- (+) Explore different paths without side effects
- (+) Suggestions available at each step
- (+) Good for UI bindings
- (-) More objects created (immutable pattern)
- (-) Slightly more verbose than mutable builders

---

## Why Exclusion Groups and Dependency Rules?

**Problem**: Arguments often have relationships (mutually exclusive, conditional requirements).

**Decision**: Declarative exclusion groups and dependency rules in the spec.

**Alternatives considered**:
- Code-based validation only: Not visible in spec, harder to generate help
- Rely on custom validators: Common patterns deserve built-in support
- No validation: Leads to confusing user errors

**Trade-offs**:
- (+) Common patterns have declarative syntax
- (+) Visible in help text
- (+) Validated at parsing time
- (-) Limited expressiveness (complex rules need custom validators)
- (-) More spec complexity

---

## Why Value Providers?

**Problem**: Some arguments have valid values that aren't known until runtime (regions, instances, users).

**Decision**: Value providers - functions that return valid values.

**Alternatives considered**:
- Static `accepts` lists: Can't handle dynamic data
- No suggestions: Poor autocompletion experience
- Shell completion scripts: Separate from spec, hard to maintain

**Trade-offs**:
- (+) Dynamic values for autocompletion
- (+) Validation against provider values
- (+) Context-aware (depends on other args)
- (-) Functions may fail or be slow
- (-) No caching by default

---

## Why Backward Compatibility?

**Problem**: How to evolve from v1.x to v2.0 without breaking existing users?

**Decision**: Full backward compatibility - v1.x specs work unchanged in v2.0.

**Alternatives considered**:
- Breaking changes with migration tool: More disruption
- Separate packages: Maintenance burden
- Deprecation period: Still eventually breaks

**Trade-offs**:
- (+) Zero migration effort for existing users
- (+) Can adopt v2.0 features incrementally
- (+) Single codebase to maintain
- (-) Must support two code paths
- (-) Schema version detection adds complexity

---

## Why `--` for Options End?

**Problem**: How to handle arguments that look like options (e.g., `--filename-with-dashes`)?

**Decision**: Follow POSIX convention - `--` marks end of options.

**Alternatives considered**:
- Quoting: Doesn't work in all shells
- Escape sequences: Non-standard
- No support: Can't handle edge cases

**Trade-offs**:
- (+) Standard, expected by users
- (+) Works in all shells
- (-) One more thing to document

---

## Why Not argparse/Click/Typer?

**Problem**: Python has excellent CLI libraries. Why build another?

**Decision**: config_loader addresses a different problem space.

**Key differences**:
- **Multi-source merging**: argparse is CLI-only
- **Declarative spec**: Click uses decorators
- **Hierarchical commands with global params**: Specific to our three-phase model
- **Protocol plugins**: Not supported elsewhere
- **Builder pattern**: For IDE integration

**When to use argparse/Click/Typer instead**:
- Simple CLI-only applications
- No need for ENV/RC file merging
- Python-only teams who prefer decorators

**When to use config_loader**:
- Complex configuration from multiple sources
- Need for declarative, language-agnostic specs
- Hierarchical commands with inheritance
- IDE integration requirements

---

## Summary of Key Principles

1. **Declarative over imperative**: Spec files over code configuration
2. **Explicit over implicit**: Scoping, precedence, and validation are declared
3. **Flexible over prescriptive**: Support multiple sources and orderings
4. **Safe by default**: Secrets are obfuscated, validation is strict
5. **Extensible over complete**: Plugins and providers instead of built-in integrations
6. **Backward compatible**: Evolve without breaking existing users

---

## See Also

- **[Architecture](architecture.md)** — Component overview
- **[Three-Phase Parsing](three-phase-parsing.md)** — Parsing model details
- **[YAML Schema Reference](../reference/yaml-schema.md)** — All configuration options
