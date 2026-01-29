# Publishing vgate to PyPI

This document describes the modern workflow for publishing the `vgate` package to PyPI.

## Prerequisites

1. **PyPI Account**: You already have a PyPI account
2. **PyPI Token**: You have a PyPI API token locally
3. **GitHub Repository**: Repository is set up on GitHub (GLEIF-IT/vgate)

## Publishing Methods

### Method 1: Automated Publishing via GitHub Actions (Recommended)

The repository includes a GitHub Actions workflow that automatically publishes to PyPI when you create a GitHub release.

#### Setup Steps:

1. **Set up Trusted Publishing (Recommended)**:
   - Go to https://pypi.org/manage/account/publishing/
   - Click "Add a new pending publisher"
   - Select "GitHub Actions"
   - Repository: `GLEIF-IT/vgate`
   - Workflow filename: `.github/workflows/publish.yml`
   - Environment name: (leave blank or use `release`)
   - Click "Add"
   - Approve the pending publisher

2. **Alternative: Use API Token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token (scope: "Entire account" or project-specific)
   - In GitHub: Settings → Secrets and variables → Actions → New repository secret
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token
   - Uncomment the API token section in `.github/workflows/publish.yml`

#### Publishing Process:

1. **Update version in `pyproject.toml`**:
   ```toml
   version = "0.1.2"  # Increment version
   ```

2. **Commit and push**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.2"
   git push origin main
   ```

3. **Create a GitHub Release**:
   - Go to GitHub → Releases → "Draft a new release"
   - Tag: `v0.1.2` (must match version in pyproject.toml)
   - Title: `v0.1.2`
   - Description: Release notes
   - Click "Publish release"
   - The workflow will automatically build and publish to PyPI

4. **Verify**:
   - Check https://pypi.org/project/vgate/
   - Install: `pip install vgate==0.1.2`

### Method 2: Manual Publishing with uv

For quick manual publishing or testing:

1. **Build the package**:
   ```bash
   uv build
   ```
   This creates distribution files in `dist/` directory.

2. **Publish to PyPI**:
   ```bash
   # Using uv (recommended)
   uv publish --token YOUR_PYPI_API_TOKEN
   
   # Or using twine (if you prefer)
   pip install twine
   twine upload dist/*
   ```

3. **Verify**:
   ```bash
   pip install vgate --upgrade
   ```

### Method 3: Test Publishing to TestPyPI First

Always test on TestPyPI before publishing to production:

1. **Create TestPyPI account** (if you don't have one):
   - Go to https://test.pypi.org/account/register/

2. **Get TestPyPI token**:
   - Go to https://test.pypi.org/manage/account/token/

3. **Publish to TestPyPI**:
   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/ \
     --token YOUR_TESTPYPI_TOKEN
   ```

4. **Test installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ vgate
   ```

## Version Management

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 0.1.2)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Update version in `pyproject.toml` before each release.

## Pre-release Checklist

Before publishing:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` (if you maintain one)
- [ ] Run tests: `uv run pytest`
- [ ] Run linting: `make check`
- [ ] Build locally: `uv build` (verify no errors)
- [ ] Test installation: `pip install dist/vgate-*.whl`
- [ ] Update README if needed
- [ ] Commit and tag: `git tag v0.1.2`

## Troubleshooting

### "Package already exists" error
- Version already published. Increment version in `pyproject.toml`.

### "Invalid credentials" error
- Check your PyPI token is valid
- For trusted publishing, verify GitHub Actions setup

### Build fails
- Ensure `src/vgate/` directory exists (not `src/viking/`)
- Check `pyproject.toml` has correct package path
- Run `uv build` locally to debug

## Additional Resources

- [PyPI Documentation](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [uv Publishing Guide](https://docs.astral.sh/uv/publishing/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
