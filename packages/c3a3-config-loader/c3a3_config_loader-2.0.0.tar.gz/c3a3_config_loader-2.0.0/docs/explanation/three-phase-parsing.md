# Three-Phase Parsing

How config_loader parses hierarchical commands.

---

## Overview

The v2.0 command system uses a three-phase parsing approach:

1. **Phase 1**: Extract global parameters
2. **Phase 2**: Resolve command path
3. **Phase 3**: Bind command arguments

This design allows global parameters and command arguments to coexist without ambiguity.

---

## The Problem

Consider this input:

```bash
myapp --verbose deploy staging --region us-east-1
```

We need to determine:
- Is `--verbose` a global parameter or a command argument?
- Which command does `--region` belong to?
- Where does the command path end?

Traditional single-pass parsers struggle with this. The three-phase approach solves it by separating concerns.

---

## Token Classification

Before parsing begins, the tokenizer classifies each input token:

| Token | Type | Notes |
|-------|------|-------|
| `--` | OPTIONS_END | Marks end of options |
| `--name` | LONG_OPTION | May include `=value` |
| `-x` | SHORT_OPTION | May be bundled (`-xyz`) |
| `deploy` | COMMAND | Matches command tree |
| `us-east-1` | POSITIONAL | Everything else |

The tokenizer builds an index of all command names and aliases across all levels of the tree for fast lookup.

```
Input: ["--verbose", "deploy", "staging", "--region", "us-east-1"]

Tokens:
  [0] LONG_OPTION  value="verbose"      original="--verbose"
  [1] COMMAND      value="deploy"       original="deploy"
  [2] COMMAND      value="staging"      original="staging"
  [3] LONG_OPTION  value="region"       original="--region"
  [4] POSITIONAL   value="us-east-1"    original="us-east-1"
```

---

## Phase 1: Extract Global Parameters

Global parameters are those defined in the `parameters` section of the spec. They can appear anywhere in the input.

```yaml
parameters:
  - namespace: null
    name: verbose
    type: boolean
```

Phase 1 scans all tokens, extracts those matching global parameters, and passes the rest to Phase 2.

```
Input Tokens:
  [0] LONG_OPTION  "verbose"    ← matches global parameter
  [1] COMMAND      "deploy"
  [2] COMMAND      "staging"
  [3] LONG_OPTION  "region"
  [4] POSITIONAL   "us-east-1"

After Phase 1:
  Global: [LONG_OPTION "verbose"]
  Remaining: [COMMAND "deploy", COMMAND "staging", LONG_OPTION "region", POSITIONAL "us-east-1"]
```

This allows users to place global parameters anywhere:

```bash
# All equivalent:
myapp --verbose deploy staging
myapp deploy --verbose staging
myapp deploy staging --verbose
```

---

## Phase 2: Resolve Command Path

Phase 2 walks the remaining tokens, building the command path through the tree.

```
Command Tree:
  deploy (non-terminal)
  ├── staging (terminal)
  └── production (terminal)
```

Starting at root, each COMMAND token is checked against available subcommands:

```
Position: root
  Token "deploy" → matches "deploy" → path = ["deploy"]

Position: deploy
  Token "staging" → matches "staging" → path = ["deploy", "staging"]

Position: staging (terminal)
  Token "--region" → option, not a command
  Token "us-east-1" → positional

Result:
  Command Path: ["deploy", "staging"]
  Argument Tokens: [LONG_OPTION "region"]
  Positional Tokens: [POSITIONAL "us-east-1"]
```

### Ordering Modes

Commands can specify how strictly arguments must follow commands:

| Mode | Behavior |
|------|----------|
| `strict` | Arguments must appear after the command |
| `relaxed` | Arguments can appear before or after (default) |
| `interleaved` | Arguments can be mixed with subcommands |

With `ordering: strict`:

```bash
myapp --region us-east-1 deploy   # Error: argument before command
myapp deploy --region us-east-1   # OK
```

With `ordering: relaxed` (default):

```bash
myapp --region us-east-1 deploy   # OK
myapp deploy --region us-east-1   # OK
```

---

## Phase 3: Bind Command Arguments

Phase 3 matches argument tokens against the resolved command's argument scope.

### Building the Argument Scope

The scope includes:
1. **Inherited arguments** from ancestor commands
2. **Local arguments** from the final command

```yaml
commands:
  - name: deploy
    arguments:
      - name: verbose
        scope: inherited    # Available to all subcommands

    subcommands:
      - name: staging
        terminal: true
        arguments:
          - name: region
            scope: local    # Only available in staging
```

For path `["deploy", "staging"]`:

```
Scope:
  verbose (inherited from deploy)
  region (local to staging)
```

### Argument Resolution

Each argument token is matched against the scope:

```
Token: LONG_OPTION "region"
  → Matches CommandArgument(name="region", type="string", required=True)
  → Next token POSITIONAL "us-east-1" consumed as value

Result:
  arguments = {"region": "us-east-1"}
```

### Short Flag Handling

Short flags can reference arguments with a `short` field:

```yaml
arguments:
  - name: region
    short: r
    type: string
```

```bash
myapp deploy staging -r us-east-1
```

Bundled flags expand:

```bash
myapp deploy staging -vvv    # → verbose=3 (if counting enabled)
myapp deploy staging -rf     # → region, force (if both are booleans)
```

### Environment Variables

Arguments with `env: true` are checked after CLI parsing:

```yaml
arguments:
  - name: region
    env: true
    env_name: AWS_REGION  # Optional custom name
```

Order of precedence for argument values:
1. CLI (explicit argument)
2. Environment variable (if `env: true`)
3. Default value

### Validation

After binding, Phase 3 validates:
- **Required arguments** are present
- **Exclusion groups** are not violated
- **Dependency rules** are satisfied
- **Custom validators** pass
- **Value providers** validate input

---

## Complete Example

Input:

```bash
myapp --db.host localhost deploy staging --region us-east-1 --force
```

Spec:

```yaml
parameters:
  - namespace: db
    name: host
    type: string

commands:
  - name: deploy
    subcommands:
      - name: staging
        terminal: true
        arguments:
          - name: region
            type: string
            required: true
          - name: force
            short: f
            type: boolean
```

### Tokenization

```
Tokens:
  [0] LONG_OPTION  "db.host"
  [1] POSITIONAL   "localhost"
  [2] COMMAND      "deploy"
  [3] COMMAND      "staging"
  [4] LONG_OPTION  "region"
  [5] POSITIONAL   "us-east-1"
  [6] LONG_OPTION  "force"
```

### Phase 1: Extract Global Parameters

```
Global Parameters: ["db.host"] matches parameters[0]
  → Extract [LONG_OPTION "db.host", POSITIONAL "localhost"]
  → Result: {"db": {"host": "localhost"}}

Remaining: [COMMAND "deploy", COMMAND "staging", LONG_OPTION "region",
            POSITIONAL "us-east-1", LONG_OPTION "force"]
```

### Phase 2: Resolve Command Path

```
root → "deploy" matches → path = ["deploy"]
deploy → "staging" matches → path = ["deploy", "staging"]
staging (terminal) → collect remaining tokens

Result:
  path = ["deploy", "staging"]
  arg_tokens = [LONG_OPTION "region", LONG_OPTION "force"]
  positional_tokens = [POSITIONAL "us-east-1"]
```

### Phase 3: Bind Command Arguments

```
Scope for ["deploy", "staging"]:
  region (local, required)
  force (local, boolean)

Binding:
  "region" → type=string → consumes "us-east-1" → {"region": "us-east-1"}
  "force" → type=boolean → true → {"force": true}

Validation:
  ✓ region is required and present
  ✓ No exclusion violations
  ✓ No dependency violations

Result:
  arguments = {"region": "us-east-1", "force": True}
  positional = []
```

### Final Result

```python
ProcessingResult:
  config:
    db.host = "localhost"

  command:
    path = ["deploy", "staging"]
    arguments = {"region": "us-east-1", "force": True}
    positional = []
    terminal = True
```

---

## Error Recovery

When parsing fails, the parser provides helpful errors:

### Unknown Command

```
Input: myapp depoly staging

Error: Unknown command 'depoly' at (root). Available: deploy, rollback
Did you mean: deploy
```

### Non-Terminal Command

```
Input: myapp deploy

Error: 'deploy' is not a complete command. Continue with: staging, production
```

### Missing Required Argument

```
Input: myapp deploy staging

Error: Required argument '--region' not provided for command 'deploy staging'
```

### Invalid Argument

```
Input: myapp deploy staging --regin us-east-1

Error: Unknown argument '--regin' for command 'deploy staging'.
Available: --region, --force
Did you mean: --region
```

---

## Performance Considerations

- **Token classification**: O(n) where n = number of arguments
- **Command lookup**: O(1) using pre-built index
- **Argument scope building**: O(d) where d = path depth
- **Overall**: O(n + d) - linear in input size and path depth

The pre-built command index avoids scanning the command tree during parsing.

---

## See Also

- **[Architecture](architecture.md)** — Component overview
- **[Design Decisions](design-decisions.md)** — Why three phases?
- **[CLI Conventions](../reference/cli-conventions.md)** — Argument syntax
