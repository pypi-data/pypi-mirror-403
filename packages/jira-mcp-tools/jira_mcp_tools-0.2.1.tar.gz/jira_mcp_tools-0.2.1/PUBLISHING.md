# Publishing mcp-jira to PyPI

This guide explains how to publish the mcp-jira package to PyPI.

## Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org/account/register/
   - Verify your email address

2. **PyPI API Token**
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with scope "Entire account"
   - Save the token securely (starts with `pypi-`)

3. **Install Build Tools**
   ```bash
   pip install build twine
   ```

## Publishing Steps

### 1. Prepare the Release

Update version in `pyproject.toml`:
```toml
version = "0.1.2"  # Increment version
```

### 2. Build the Package

```bash
cd /path/to/mcp-jira
python -m build
```

This creates:
- `dist/mcp_jira-0.1.2-py3-none-any.whl`
- `dist/mcp-jira-0.1.2.tar.gz`

### 3. Test on TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ mcp-jira
```

### 4. Upload to PyPI

```bash
twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: Your PyPI API token (including `pypi-` prefix)

### 5. Verify Installation

```bash
# Install from PyPI
pip install mcp-jira

# Or with uvx
uvx mcp-jira
```

## Using API Token in CI/CD

For automated publishing, store the token as a secret:

### GitHub Actions

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Version Management

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Examples:
- `0.1.1` → `0.1.2` (bug fix)
- `0.1.2` → `0.2.0` (new feature)
- `0.2.0` → `1.0.0` (stable release)

## Troubleshooting

### "File already exists" Error

You cannot re-upload the same version. Increment the version number.

### Authentication Failed

- Ensure username is `__token__`
- Verify token includes `pypi-` prefix
- Check token hasn't expired

### Package Name Conflict

If `mcp-jira` is taken, choose alternative:
- `mcp-jira-server`
- `jira-mcp-server`
- `ibm-mcp-jira`

## Post-Publishing

1. **Create GitHub Release**
   - Tag: `v0.1.2`
   - Title: `Release 0.1.2`
   - Description: Changelog

2. **Update Documentation**
   - Update README with new version
   - Update bob-marketplace-registry

3. **Announce**
   - Internal Slack channels
   - GitHub discussions
   - Documentation sites

## Resources

- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)