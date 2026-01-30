# pipes-compat

[![CI](https://github.com/Grochocinski/pipes-compat/actions/workflows/ci.yml/badge.svg)](https://github.com/Grochocinski/pipes-compat/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pipes-compat.svg)](https://pypi.org/project/pipes-compat/)
[![Python versions](https://img.shields.io/pypi/pyversions/pipes-compat.svg)](https://pypi.org/project/pipes-compat/)
[![License](https://img.shields.io/pypi/l/pipes-compat.svg)](https://github.com/Grochocinski/pipes-compat/blob/main/LICENSE)

A drop-in compatibility shim for Python's removed `pipes` module.

## Why Use This?

The `pipes` module was deprecated in Python 3.11 and **removed in Python 3.13** as part of [PEP 594](https://peps.python.org/pep-0594/) (Removing dead batteries from the standard library).

This package exists for one purpose: **to help you migrate legacy code to Python 3.13+ without rewriting every `import pipes` statement**.

**Use this if:**
- You have existing code that uses `pipes.quote()` or `pipes.Template`
- You're upgrading a project to Python 3.13+ and need a quick fix
- You depend on a library that hasn't been updated yet

**For new code:** Use `shlex.quote()` directly for shell escaping, or `subprocess` for running shell commands.

## Installation

```bash
pip install pipes-compat
```

Or with uv:

```bash
uv add pipes-compat
```

## Quick Start

This package is designed as a **drop-in replacement**. Your existing code should work unchanged:

```python
import pipes

# Shell-escape a string (most common use case)
escaped = pipes.quote("file with spaces.txt")
print(escaped)  # 'file with spaces.txt'

# Build and execute a shell pipeline
t = pipes.Template()
t.append("grep -v '^#'", "--")      # Remove comment lines
t.append("tr a-z A-Z", "--")        # Convert to uppercase
t.append("sort -u", "--")           # Sort and deduplicate
t.copy("input.txt", "output.txt")   # Execute the pipeline
```

## Step Kinds

When adding commands to a pipeline with `append()` or `prepend()`, you must specify a **kind** that describes how the command handles input and output:

| Kind | Name | Input | Output | Description |
|------|------|-------|--------|-------------|
| `--` | STDIN_STDOUT | stdin | stdout | Normal pipeline command (most common) |
| `f-` | FILEIN_STDOUT | file (`$IN`) | stdout | Reads from a file, writes to stdout |
| `-f` | STDIN_FILEOUT | stdin | file (`$OUT`) | Reads from stdin, writes to a file |
| `ff` | FILEIN_FILEOUT | file (`$IN`) | file (`$OUT`) | Reads from and writes to files |
| `.-` | SOURCE | (generates) | stdout | Generates output, must be first step |
| `-.` | SINK | stdin | (consumes) | Consumes input, must be last step |

### Using `$IN` and `$OUT` Placeholders

Commands with file-based kinds (`f-`, `-f`, `ff`) must include `$IN` and/or `$OUT` placeholders:

```python
import pipes

t = pipes.Template()

# File input: command must contain $IN
t.append("cat $IN | grep error", "f-")

# File output: command must contain $OUT  
t.append("sort > $OUT", "-f")

# Both: command must contain both $IN and $OUT
t.append("cat $IN | sort > $OUT", "ff")
```

The placeholders are replaced with actual filenames (properly quoted) when the pipeline executes.

### SOURCE and SINK

SOURCE commands generate output without reading input (must be first):

```python
t = pipes.Template()
t.prepend("echo 'hello world'", ".-")  # SOURCE: generates output
t.append("tr a-z A-Z", "--")
t.copy("", "output.txt")  # Empty string for input since SOURCE generates it
```

SINK commands consume input without producing output (must be last):

```python
t = pipes.Template()
t.append("wc -l", "-.")  # SINK: consumes input
t.copy("input.txt", "")  # Empty string for output since SINK consumes it
```

## API Reference

### `pipes.quote(s: str) -> str`

Return a shell-escaped version of the string. This is equivalent to `shlex.quote()`.

```python
>>> pipes.quote("hello world")
"'hello world'"
>>> pipes.quote("it's")
"'it'\"'\"'s'"
```

### `pipes.Template`

A class for building and executing shell pipelines.

#### Constructor

```python
t = pipes.Template()
```

Creates a new, empty pipeline template.

#### Methods

| Method | Description |
|--------|-------------|
| `append(cmd, kind)` | Add a command to the end of the pipeline |
| `prepend(cmd, kind)` | Add a command to the beginning of the pipeline |
| `copy(infile, outfile) -> int` | Execute the pipeline, returns exit status |
| `open(file, mode)` | Open a file through the pipeline (`'r'` or `'w'`) |
| `open_r(file)` | Open a file for reading through the pipeline |
| `open_w(file)` | Open a file for writing through the pipeline |
| `clone() -> Template` | Return a copy of the template |
| `reset()` | Clear all steps from the template |
| `debug(flag)` | Enable/disable debug output (prints commands to stdout) |
| `makepipeline(infile, outfile) -> str` | Return the shell command without executing |

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `steps` | `list[tuple[str, str]]` | List of (command, kind) tuples |
| `debugging` | `object` | Current debug flag value |

### Constants

The module exports step kind constants for convenience:

```python
import pipes

pipes.FILEIN_FILEOUT  # "ff"
pipes.STDIN_FILEOUT   # "-f"
pipes.FILEIN_STDOUT   # "f-"
pipes.STDIN_STDOUT    # "--"
pipes.SOURCE          # ".-"
pipes.SINK            # "-."

pipes.stepkinds  # List of all valid kinds
```

## Examples

### Reading a File Through a Pipeline

```python
import pipes

t = pipes.Template()
t.append("tr a-z A-Z", "--")
t.append("head -n 10", "--")

# Read file through the pipeline
f = t.open("input.txt", "r")
content = f.read()
f.close()
print(content)
```

### Writing Through a Pipeline

```python
import pipes

t = pipes.Template()
t.append("tr a-z A-Z", "--")

# Write to file through the pipeline
f = t.open("output.txt", "w")
f.write("hello world\n")
f.close()
# output.txt now contains "HELLO WORLD\n"
```

### Cloning and Modifying Templates

```python
import pipes

base = pipes.Template()
base.append("tr a-z A-Z", "--")

# Create variations
version1 = base.clone()
version1.append("head -n 5", "--")

version2 = base.clone()
version2.append("tail -n 5", "--")

# Use independently
version1.copy("input.txt", "first5_upper.txt")
version2.copy("input.txt", "last5_upper.txt")
```

### Debugging Pipelines

```python
import pipes

t = pipes.Template()
t.debug(True)  # Enable debug output
t.append("grep error", "--")
t.append("wc -l", "--")

# This prints the shell command before executing
t.copy("logfile.txt", "error_count.txt")
```

## Migration from Python 3.12

If you're upgrading from Python 3.12 or earlier:

1. **Install pipes-compat**: `pip install pipes-compat`
2. **No code changes needed** - your existing `import pipes` statements will work
3. **Gradually migrate** to `shlex.quote()` and `subprocess` when convenient

### Before (Python 3.12)

```python
import pipes  # From standard library

escaped = pipes.quote(filename)
```

### After (Python 3.13+)

```python
import pipes  # From pipes-compat (drop-in replacement)

escaped = pipes.quote(filename)
```

Or migrate to the recommended approach:

```python
import shlex

escaped = shlex.quote(filename)
```

## Requirements

- Python 3.13 or later
- Unix-like operating system (uses `/bin/sh` for command execution)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/Grochocinski/pipes-compat.git
cd pipes-compat

# Install dependencies with uv
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pipes --cov-report=term-missing

# Run tests with coverage threshold
uv run pytest --cov=pipes --cov-fail-under=90
```

### Linting and Type Checking

```bash
# Run ruff linter
uv run ruff check .

# Run ruff formatter
uv run ruff format --check .

# Run ty type checker
uv run ty check

# Auto-fix linting issues
uv run ruff check --fix .
uv run ruff format .
```

## License

Apache-2.0

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

When contributing, please:
1. Add tests for new functionality
2. Ensure all tests pass and coverage remains above 90%
3. Run `uv run pre-commit run --all-files` before submitting
