# 📦 Publishing to PyPI

This guide explains how to publish `pybob-sdk` to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org) if you don't have one
2. **API Token**: Create an API token at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
   - For test releases, use [test.pypi.org](https://test.pypi.org)
3. **uv**: Ensure `uv` is installed (you're already using it!)

## Quick Start

### Option 1: Using the publish script (Recommended)

```bash
# Update version and publish
./scripts/publish.sh 0.1.1
```

The script will:
- Update the version in `pyproject.toml`
- Clean previous builds
- Build the package
- Prompt you to publish

### Option 2: Manual steps

#### 1. Update version

Edit `pyproject.toml` and update the version:

```toml
[project]
version = "0.1.1"  # Update this
```

#### 2. Clean previous builds

```bash
rm -rf dist/ build/ *.egg-info
```

#### 3. Build the package

```bash
uv build
```

This creates distribution files in the `dist/` directory:
- `pybob_sdk-0.1.1-py3-none-any.whl` (wheel)
- `pybob_sdk-0.1.1.tar.gz` (source distribution)

#### 4. Verify the build

```bash
# Check what will be published
ls -lh dist/

# Optionally, test install locally
pip install dist/pybob_sdk-0.1.1-py3-none-any.whl
```

#### 5. Publish to PyPI

**Using uv (recommended):**

```bash
uv publish
```

**Using twine (alternative):**

```bash
# Install twine if needed
pip install twine

# Publish
twine upload dist/*
```

#### 6. Authenticate

When prompted, use your PyPI credentials:
- **Username**: `__token__`
- **Password**: Your PyPI API token (starts with `pypi-`)

Or set environment variables:

```bash
export UV_PUBLISH_USERNAME=__token__
export UV_PUBLISH_PASSWORD=pypi-your-api-token-here
```

## Testing on TestPyPI

Before publishing to production PyPI, test on TestPyPI:

```bash
# Build first
uv build

# Publish to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pybob-sdk
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., `1.0.0`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Post-Publishing Checklist

- [ ] Verify package appears on [pypi.org/project/pybob-sdk](https://pypi.org/project/pybob-sdk)
- [ ] Test installation: `pip install pybob-sdk==<version>`
- [ ] Update release notes in GitHub (if applicable)
- [ ] Tag the release: `git tag v<version> && git push --tags`

## Troubleshooting

### "Package already exists"
- The version number must be unique. Increment the version in `pyproject.toml`.

### "Authentication failed"
- Verify your API token is correct
- Ensure you're using `__token__` as the username
- Check token permissions (should have "Upload packages" scope)

### "Build failed"
- Ensure all dependencies are listed in `pyproject.toml`
- Check that `pybob_sdk/` directory structure is correct
- Verify `__init__.py` files exist in all packages

## Automated Publishing (GitHub Actions)

Consider setting up GitHub Actions for automated publishing on tags:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - run: uv publish
        env:
          UV_PUBLISH_USERNAME: __token__
          UV_PUBLISH_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```
