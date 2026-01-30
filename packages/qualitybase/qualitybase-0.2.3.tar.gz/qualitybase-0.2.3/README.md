# python-qualitybase

Qualitybase is a Python library that provides standardized services and tooling for managing code quality, development workflows, and project maintenance in Python projects.

## Installation

```bash
pip install qualitybase
```

For development:

```bash
pip install -e .
pip install -e ".[dev,lint,quality,security,test]"
```

## Usage

Qualitybase provides a unified entry point via the `service.py` script:

```bash
./service.py <service> <command>
```

### Available Services

- **`quality`**: Quality checks (lint, security, test, complexity, cleanup)
- **`dev`**: Development tools (venv, install, clean, build, etc.)
- **`django`**: Django-specific services
- **`publish`**: Package publishing and distribution
- **`cli`**: Command-line interface for packages

### Examples

```bash
# Quality checks
./service.py quality lint
./service.py quality security
./service.py quality all

# Development tools
./service.py dev venv
./service.py dev install-dev
./service.py dev clean

# Help
./service.py quality help
./service.py dev help
```

## CLI System

Qualitybase includes a flexible CLI system that allows packages to define custom commands through a `commands` directory.

### Command Discovery

The CLI system automatically discovers commands from:

1. **`commands/` directory**: A directory next to `cli.py` containing command modules
2. **`.commands.json` configuration file**: A JSON file that can specify:
   - `packages`: List of packages to discover commands from
   - `directories`: List of directories to scan for commands
   - `commands`: Direct command definitions

### Creating Commands

Commands can be created in two ways:

#### Method 1: Using the `Command` class

Create a file in the `commands/` directory (e.g., `commands/mycommand.py`):

```python
from .base import Command

def _mycommand_command(args: list[str]) -> bool:
    """Description of what this command does."""
    # Command implementation
    print("Hello from mycommand!")
    return True

mycommand_command = Command(_mycommand_command, "Description of what this command does")
```

The command will be automatically discovered and available as:
```bash
./service.py cli mycommand
```

#### Method 2: Using functions ending with `_command`

```python
def mycommand_command(args: list[str]) -> bool:
    """Description of what this command does."""
    # Command implementation
    print("Hello from mycommand!")
    return True
```

### Command Naming

- Functions ending with `_command` are automatically discovered
- The command name is derived from the function name (removing `_command` suffix)
- Private functions (starting with `_`) have the underscore removed
- `Command` instances can use any name, but follow similar naming conventions

### Command Structure

Commands receive a list of string arguments and return a boolean indicating success:

```python
def mycommand_command(args: list[str]) -> bool:
    """Command description for help text."""
    if not args:
        print("Usage: mycommand <arg1> <arg2>")
        return False
    
    # Process arguments
    arg1 = args[0]
    # ... command logic ...
    
    return True  # Success
```

### Built-in Commands

Qualitybase provides several built-in commands in `qualitybase/commands/`:

- **`help`**: Display available commands
- **`version`**: Show package version information
- **`varenv`**: Show or manage environment variables

### Example: Custom Command

Create `src/mypackage/commands/greet.py`:

```python
from .base import Command

def greet_command(args: list[str]) -> bool:
    """Greet someone by name."""
    if not args:
        print("Usage: greet <name>")
        return False
    
    name = args[0]
    print(f"Hello, {name}!")
    return True

greet_command = Command(greet_command, "Greet someone by name")
```

Then use it:
```bash
./service.py cli greet Alice
# Output: Hello, Alice!
```

### Configuration File

You can configure command discovery using `.commands.json`:

```json
{
    "packages": ["otherpackage"],
    "directories": ["custom_commands"],
    "commands": []
}
```

## Environment Variables

### `ENVFILE_PATH`

The `ENVFILE_PATH` environment variable allows you to automatically specify the path to a `.env` file to load when starting services.

**Usage:**

```bash
# Absolute path
ENVFILE_PATH=/path/to/.env ./service.py dev install-dev

# Relative path (relative to project root)
ENVFILE_PATH=.env.local ./service.py quality lint
```

**Behavior:**

- If the path is relative, it is resolved relative to the project root
- The `.env` file is automatically loaded before command execution
- Uses `python-dotenv` to parse the file (installed automatically if needed)
- Works with `dev` and `cli` services

**Example:**

```bash
# Create a .env.local file
echo "API_KEY=secret123" > .env.local

# Use this file
ENVFILE_PATH=.env.local ./service.py dev install-dev
```

### `ENSURE_VIRTUALENV`

The `ENSURE_VIRTUALENV` environment variable allows you to automatically activate the `.venv` virtual environment if it exists, before executing commands.

**Usage:**

```bash
ENSURE_VIRTUALENV=1 ./service.py dev help
ENSURE_VIRTUALENV=1 ./service.py quality lint
```

**Behavior:**

- Must be set to `1` to be active
- Automatically activates the `.venv` virtual environment at the project root
- Modifies `sys.executable`, `PATH`, and `sys.path` to use the venv's Python
- Only works if the `.venv` directory exists
- Compatible with Windows and Unix

**Note:** The `ensure_virtualenv()` function is also automatically called by the main service, but `ENSURE_VIRTUALENV` allows you to force activation even in contexts where it might not be automatic.

**Example:**

```bash
# Create a virtual environment
python -m venv .venv

# Use it automatically
ENSURE_VIRTUALENV=1 ./service.py quality all
```

## Architecture

Qualitybase uses a service-based architecture:

- Each service domain is organized in its own module directory
- Services are accessed through a unified entry point (`service.py`)
- Services can be invoked via `./service.py <service> <command>` or directly via Python modules
- The system ensures virtual environment setup and proper dependency management
- Services are designed to work consistently across different Python projects

## Development

See `docs/` for project rules and guidelines.
