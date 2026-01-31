# Publishing to PyPI

## TestPyPI (for testing)

1. **Create a TestPyPI account** at https://test.pypi.org/account/register/
2. **Create an API token** at https://test.pypi.org/manage/account/token/

3. **Build and upload your package**:

```bash
# Install twine for uploading
uv pip install twine

# Build the package
uv build

# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*

# Publish to PyPI:
uv run twine upload dist/*
```

When prompted, use:
- **Username:** `__token__`
- **Password:** Your API token (including the `pypi-` prefix)

4. **Test installation from TestPyPI**:

```bash
uv add --extra-index-url https://test.pypi.org/simple/ --index-strategy unsafe-best-match paxx
```

**Tip:** You can save your credentials in `~/.pypirc`:

```ini
[testpypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

## PyPI (production)

1. **Create a PyPI account** at https://pypi.org/account/register/
2. **Create an API token** at https://pypi.org/manage/account/token/

3. **Build and upload**:

```bash
uv build
uv run twine upload dist/*
```

4. **Install from PyPI**:

```bash
pip install paxx
```
