# Testing paxx

## Unit Tests

Run the test suite:

```bash
uv run pytest -v
```

## E2E Testing

To test paxx end-to-end without publishing to PyPI:

### Option 1: Use `uv run` from project directory (recommended)

```bash
# From the project root, uv run uses the local package
cd /Users/adam/Coding/paxx
uv run paxx --version

# To test from another directory, specify the project path
cd /tmp
mkdir test-project
cd test-project
uv run --project /Users/adam/Coding/paxx paxx --version
```

This is the best option for development - changes to the source code are reflected immediately.

### Option 2: Activate the virtual environment

```bash
cd /Users/adam/Coding/paxx
source .venv/bin/activate

# Now paxx is available directly
paxx --version

# Works from any directory while venv is active
cd /tmp
paxx --version
```

### Option 3: Use `uvx` with local path

```bash
uvx --from /Users/adam/Coding/paxx paxx --version
```

### Option 4: Build and install the wheel

```bash
# Build
cd /Users/adam/Coding/paxx
uv build

# Install in a fresh environment
cd /tmp
mkdir test-project && cd test-project
uv init
uv pip install /Users/adam/Coding/paxx/dist/paxx-0.1.0-py3-none-any.whl
uv run paxx --version
```
