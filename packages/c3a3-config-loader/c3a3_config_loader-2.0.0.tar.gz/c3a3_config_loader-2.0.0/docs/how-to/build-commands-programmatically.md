# How to Build Commands Programmatically

Use the builder pattern for interactive CLI construction, IDE integrations, and wizards.

---

## Overview

The builder pattern provides a fluent API for constructing commands incrementally. It's useful for:

- **Autocompletion**: Suggest what comes next
- **IDE integrations**: Build commands in a UI
- **CLI wizards**: Interactive step-by-step flows
- **Validation**: Check commands before executing

---

## Getting Started

### Create a Builder

```python
from config_loader import Configuration

spec = {
    "schema_version": "2.0",
    "app_name": "deploy",
    "commands": [
        {
            "name": "deploy",
            "terminal": True,
            "arguments": [
                {"name": "region", "type": "string", "required": True},
                {"name": "force", "short": "f", "type": "boolean"},
            ]
        }
    ]
}

cfg = Configuration(spec)
builder = cfg.builder()
```

### Check What's Available

```python
suggestions = builder.check_next()

print(suggestions.is_valid)     # False (no command selected)
print(suggestions.commands)     # [CommandSuggestion(name="deploy", ...)]
print(suggestions.arguments)    # []
print(suggestions.errors)       # []
```

### Add Commands and Arguments

```python
# Add the deploy command
builder = builder.add_command("deploy")

# Check suggestions again
suggestions = builder.check_next()
print(suggestions.is_valid)     # False (missing required --region)
print(suggestions.arguments)    # [ArgumentSuggestion(name="region", required=True), ...]

# Add required argument
builder = builder.add_argument("region", "us-east-1")

# Now it's valid
suggestions = builder.check_next()
print(suggestions.is_valid)     # True
```

### Build the Result

```python
result = builder.build()
print(result.command.path)       # ["deploy"]
print(result.command.arguments)  # {"region": "us-east-1"}
```

---

## Immutable Builders

Each method returns a new builder instance, leaving the original unchanged:

```python
builder1 = cfg.builder()
builder2 = builder1.add_command("deploy")
builder3 = builder2.add_argument("region", "us-east-1")

# All three are independent
print(builder1.command_path)  # []
print(builder2.command_path)  # ["deploy"]
print(builder3.command_path)  # ["deploy"]
```

This enables exploring different paths:

```python
base = cfg.builder().add_command("deploy")

option_a = base.add_argument("region", "us-east-1")
option_b = base.add_argument("region", "eu-west-1")
```

---

## Using Suggestions

### Command Suggestions

```python
@dataclass
class CommandSuggestion:
    name: str                    # Command name
    aliases: List[str]           # Alternative names
    description: Optional[str]   # Human-readable description
    terminal: bool               # Can be executed?
```

```python
for cmd in suggestions.commands:
    prefix = "[terminal]" if cmd.terminal else "[namespace]"
    aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
    print(f"  {prefix} {cmd.name}{aliases}")
```

### Argument Suggestions

```python
@dataclass
class ArgumentSuggestion:
    name: str                          # Argument name
    short: Optional[str]               # Short flag (e.g., "r")
    arg_type: str                      # string, number, boolean
    required: bool                     # Is required?
    expects_value: bool                # Needs a value?
    default: Any                       # Default value
    value_suggestions: List[str]       # Suggested values
```

```python
for arg in suggestions.arguments:
    flags = f"--{arg.name}"
    if arg.short:
        flags += f", -{arg.short}"

    status = "[required]" if arg.required else "[optional]"

    if arg.value_suggestions:
        values = ", ".join(arg.value_suggestions[:3])
        print(f"  {flags} {arg.arg_type} {status} (e.g., {values})")
    else:
        print(f"  {flags} {arg.arg_type} {status}")
```

---

## Value Suggestions

Get suggestions for a specific argument:

```python
# Start setting an argument
arg_builder = builder.add_argument_builder("region")

# Get value suggestions
value_suggestions = arg_builder.check_next()
print(value_suggestions.argument_name)  # "region"
print(value_suggestions.values)          # ["us-east-1", "us-west-2", ...]
print(value_suggestions.accepts_any)     # False if restricted to values
print(value_suggestions.arg_type)        # "string"

# Set the value and return to main builder
arg_builder.set_value("us-east-1")
builder = arg_builder.build()
```

This is useful for creating dropdown menus in UIs.

---

## Handling Subcommands

Navigate through command hierarchies:

```python
spec = {
    "schema_version": "2.0",
    "app_name": "myapp",
    "commands": [
        {
            "name": "deploy",
            "subcommands": [
                {"name": "staging", "terminal": True},
                {"name": "production", "terminal": True}
            ]
        }
    ]
}

cfg = Configuration(spec)
builder = cfg.builder()

# At root level
suggestions = builder.check_next()
print(suggestions.commands)  # [deploy]

# Add first command
builder = builder.add_command("deploy")
suggestions = builder.check_next()
print(suggestions.commands)  # [staging, production]
print(suggestions.is_valid)  # False (not terminal yet)

# Add subcommand
builder = builder.add_command("staging")
suggestions = builder.check_next()
print(suggestions.is_valid)  # True (terminal command)
```

---

## Using Aliases

Aliases work the same as command names:

```python
spec = {
    "commands": [{
        "name": "deploy",
        "aliases": ["d", "push"],
        "terminal": True
    }]
}

cfg = Configuration(spec)
builder = cfg.builder()

# All of these work
builder = builder.add_command("deploy")
# or
builder = builder.add_command("d")
# or
builder = builder.add_command("push")

# Command path uses canonical name
print(builder.command_path)  # ["deploy"]
```

---

## Error Handling

### Validation Errors

```python
suggestions = builder.check_next()
if suggestions.errors:
    for error in suggestions.errors:
        print(f"Error: {error}")
    # ["Missing required argument: --region"]
```

### Invalid Operations

```python
try:
    builder.add_command("nonexistent")
except ValueError as e:
    print(e)  # "Unknown command 'nonexistent'. Available: deploy, rollback"

try:
    builder.add_argument("unknown")
except ValueError as e:
    print(e)  # "Unknown argument 'unknown'. Available: region, force"

try:
    builder.build()  # Without required args
except ValueError as e:
    print(e)  # "Missing required argument: --region"
```

---

## Complete Example: Interactive Wizard

```python
def run_wizard():
    """Interactive command builder wizard."""
    cfg = Configuration(load_spec())
    builder = cfg.builder()

    while True:
        suggestions = builder.check_next()

        # Show current state
        if builder.command_path:
            print(f"\nCurrent: {' '.join(builder.command_path)}")
            if builder.arguments:
                print(f"Arguments: {builder.arguments}")

        # If valid, offer to execute
        if suggestions.is_valid:
            response = input("\nReady to execute? (y/n/continue): ")
            if response.lower() == 'y':
                result = builder.build()
                return result
            elif response.lower() == 'n':
                return None
            # continue to add more args

        # Show available commands
        if suggestions.commands:
            print("\nAvailable commands:")
            for i, cmd in enumerate(suggestions.commands, 1):
                print(f"  {i}. {cmd.name}")

            choice = input("Select command (number or name): ")
            try:
                if choice.isdigit():
                    cmd = suggestions.commands[int(choice) - 1]
                    builder = builder.add_command(cmd.name)
                else:
                    builder = builder.add_command(choice)
            except (IndexError, ValueError) as e:
                print(f"Invalid choice: {e}")

        # Show available arguments
        elif suggestions.arguments:
            print("\nAvailable arguments:")
            for arg in suggestions.arguments:
                status = "[required]" if arg.required else ""
                print(f"  --{arg.name} {status}")

            arg_name = input("Argument name (or 'done'): ")
            if arg_name == 'done':
                if suggestions.is_valid:
                    result = builder.build()
                    return result
                else:
                    print("Cannot finish: " + "; ".join(suggestions.errors))
            else:
                arg_builder = builder.add_argument_builder(arg_name)
                value_suggestions = arg_builder.check_next()

                if value_suggestions.values:
                    print(f"Suggestions: {', '.join(value_suggestions.values[:5])}")

                value = input(f"Value for --{arg_name}: ")
                builder = builder.add_argument(arg_name, value)

        else:
            print("No more options available")
            break

    return None


if __name__ == "__main__":
    result = run_wizard()
    if result:
        print(f"\nFinal command: {result.command.path}")
        print(f"Arguments: {result.command.arguments}")
```

---

## Integration with IDEs

### Generate Completion Data

```python
def generate_completions(cfg: Configuration, partial_path: list[str] = None):
    """Generate completion data for an IDE."""
    builder = cfg.builder()

    # Navigate to current position
    if partial_path:
        for cmd in partial_path:
            try:
                builder = builder.add_command(cmd)
            except ValueError:
                break

    suggestions = builder.check_next()

    return {
        "commands": [
            {"name": c.name, "aliases": c.aliases, "terminal": c.terminal}
            for c in suggestions.commands
        ],
        "arguments": [
            {
                "name": a.name,
                "short": a.short,
                "type": a.arg_type,
                "required": a.required,
                "values": a.value_suggestions,
            }
            for a in suggestions.arguments
        ],
        "is_valid": suggestions.is_valid,
    }
```

---

## Inspecting Builder State

```python
builder = cfg.builder().add_command("deploy").add_argument("region", "us-east-1")

# Current command path
print(builder.command_path)   # ["deploy"]

# Currently set arguments
print(builder.arguments)      # {"region": "us-east-1"}

# Positional arguments
print(builder.positional)     # []
```

---

## See Also

- **[Python API Reference](../reference/python-api.md)** — Builder classes
- **[Use Value Providers](use-value-providers.md)** — Dynamic suggestions
- **[Building a CLI App](../tutorials/cli-app.md)** — Tutorial with commands
