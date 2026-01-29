# Packaging and Versioning Guide

This document provides step-by-step instructions for packaging, building, and publishing the `cph-imgclassification` package to PyPI, as well as guidelines for versioning future releases.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Building the Package](#building-the-package)
3. [Testing the Package Locally](#testing-the-package-locally)
4. [Publishing to PyPI](#publishing-to-pypi)
5. [Versioning Guidelines](#versioning-guidelines)
6. [Release Checklist](#release-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Required Tools

```bash
pip install build twine
```

### 2. Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Register with your email: `chandra385123@gmail.com`
3. Verify your email address

### 3. Create API Token

1. Log in to https://pypi.org
2. Go to Account settings → API tokens: https://pypi.org/manage/account/token/
3. Click "Add API token"
4. Name it (e.g., "cph-imgclassification")
5. Scope: Select "Entire account" or "Project: cph-imgclassification"
6. Copy the token (starts with `pypi-`) - **Save it securely, you won't see it again!**

---

## Building the Package

### Step 1: Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf cph_imgclassification.egg-info/
```

**Windows PowerShell:**
```powershell
Remove-Item -Recurse -Force build, dist, *.egg-info, cph_imgclassification.egg-info -ErrorAction SilentlyContinue
```

### Step 2: Update Version Number

Before building, update the version in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Update this for new releases
```

### Step 3: Build the Package

```bash
python -m build
```

This creates:
- `dist/cph_imgclassification-0.1.0.tar.gz` (source distribution)
- `dist/cph_imgclassification-0.1.0-py3-none-any.whl` (wheel distribution)

### Step 4: Verify Build Contents

```bash
# Check what files are included
python -m build --sdist
tar -tzf dist/cph_imgclassification-*.tar.gz | head -20

# Or on Windows PowerShell:
python -m build --sdist
Expand-Archive -Path dist\cph_imgclassification-*.tar.gz -DestinationPath temp_extract -Force
Get-ChildItem -Recurse temp_extract | Select-Object FullName
Remove-Item -Recurse -Force temp_extract
```

---

## Testing the Package Locally

### Option 1: Install in Development Mode (Recommended for Development)

```bash
pip install -e .
```

This installs the package in "editable" mode, so changes to source code are immediately reflected.

### Option 2: Install from Local Build (Test Production Install)

```bash
# Build first
python -m build

# Install from local wheel
pip install dist/cph_imgclassification-0.1.0-py3-none-any.whl

# Or install from source distribution
pip install dist/cph_imgclassification-0.1.0.tar.gz
```

### Option 3: Test on Test PyPI First

```bash
# Build the package
python -m build

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI to verify
pip install --index-url https://test.pypi.org/simple/ cph-imgclassification
```

**Note:** Test PyPI credentials are separate from PyPI. Create an account at https://test.pypi.org/

### Verify Installation

```bash
# Check if package is installed
pip show cph-imgclassification

# Test the CLI command
cph-imgclassification --help

# Test with your config
cph-imgclassification --config FoodClassification\configs\food.yaml
```

---

## Publishing to PyPI

### Step 1: Configure Authentication

**Option A: Environment Variables (Recommended)**

**Windows PowerShell:**
```powershell
$env:TWINE_USERNAME = '__token__'
$env:TWINE_PASSWORD = 'pypi-YOUR_ACTUAL_TOKEN_HERE'
```

**Linux/Mac:**
```bash
export TWINE_USERNAME='__token__'
export TWINE_PASSWORD='pypi-YOUR_ACTUAL_TOKEN_HERE'
```

**Option B: Interactive Prompt**

```bash
twine upload dist/* --username __token__ --password pypi-YOUR_TOKEN_HERE
```

**Option C: .pypirc File (Not Recommended for API Tokens)**

Create `~/.pypirc` (or `%USERPROFILE%\.pypirc` on Windows):

```ini
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

### Step 2: Check Package Name Availability

Before uploading, verify the package name is available:
- Visit: https://pypi.org/project/cph-imgclassification/

If the name is taken, update `pyproject.toml`:
```toml
[project]
name = "cph-imgclassification-chandra"  # Use a different name
```

### Step 3: Upload to PyPI

```bash
# Upload both wheel and source distribution
twine upload dist/*

# Or upload specific files
twine upload dist/cph_imgclassification-0.1.0-py3-none-any.whl dist/cph_imgclassification-0.1.0.tar.gz
```

### Step 4: Verify Upload

1. Visit: https://pypi.org/project/cph-imgclassification/
2. Check that your package appears
3. Test installation:
   ```bash
   pip install cph-imgclassification
   ```

---

## Versioning Guidelines

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/) format: `MAJOR.MINOR.PATCH`

- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### Examples

- `0.1.0` - Initial release
- `0.1.1` - Bug fix release
- `0.2.0` - New features added
- `1.0.0` - First stable release
- `1.0.1` - Critical bug fix
- `1.1.0` - New features
- `2.0.0` - Breaking changes

### Version Update Checklist

1. **Update `pyproject.toml`:**
   ```toml
   [project]
   version = "0.1.1"  # Update version
   ```

2. **Update `cph_imgclassification/__init__.py`:**
   ```python
   __version__ = "0.1.1"
   ```

3. **Update `setup.py` (if using):**
   ```python
   version="0.1.1",
   ```

4. **Update CHANGELOG.md** (create if doesn't exist):
   ```markdown
   ## [0.1.1] - 2025-01-24
   ### Fixed
   - Fixed CLI argument parsing issue
   - Resolved dependency conflicts
   ```

5. **Commit changes:**
   ```bash
   git add pyproject.toml cph_imgclassification/__init__.py CHANGELOG.md
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```

---

## Release Checklist

### Pre-Release

- [ ] Update version number in `pyproject.toml`
- [ ] Update version in `cph_imgclassification/__init__.py`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Run tests (if you have them)
- [ ] Test installation locally: `pip install -e .`
- [ ] Test CLI: `cph-imgclassification --help`
- [ ] Verify all dependencies are correct in `pyproject.toml`
- [ ] Check `README.md` is up to date
- [ ] Ensure `LICENSE` file is present
- [ ] Verify `.gitignore` excludes build artifacts

### Build

- [ ] Clean previous builds: `rm -rf build/ dist/ *.egg-info/`
- [ ] Build package: `python -m build`
- [ ] Verify build contents
- [ ] Check file sizes are reasonable

### Test Upload (Optional but Recommended)

- [ ] Upload to Test PyPI: `twine upload --repository testpypi dist/*`
- [ ] Install from Test PyPI: `pip install --index-url https://test.pypi.org/simple/ cph-imgclassification`
- [ ] Test functionality
- [ ] Fix any issues found

### Production Release

- [ ] Set PyPI credentials (environment variables or .pypirc)
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Verify package appears on PyPI
- [ ] Test installation: `pip install cph-imgclassification`
- [ ] Test CLI works: `cph-imgclassification --help`

### Post-Release

- [ ] Create GitHub release (if using GitHub)
- [ ] Tag the release: `git tag v0.1.0`
- [ ] Push tags: `git push origin --tags`
- [ ] Update documentation if needed
- [ ] Announce release (if applicable)

---

## Version Update Workflow

### For Patch Release (Bug Fixes)

```bash
# 1. Update version
# Edit pyproject.toml: version = "0.1.1"

# 2. Update CHANGELOG.md
# Add bug fixes under new version

# 3. Commit and tag
git add pyproject.toml cph_imgclassification/__init__.py CHANGELOG.md
git commit -m "Release v0.1.1 - Bug fixes"
git tag v0.1.1

# 4. Build
python -m build

# 5. Upload
twine upload dist/*

# 6. Push
git push origin main --tags
```

### For Minor Release (New Features)

```bash
# 1. Update version
# Edit pyproject.toml: version = "0.2.0"

# 2. Update CHANGELOG.md
# Document new features

# 3. Commit and tag
git add pyproject.toml cph_imgclassification/__init__.py CHANGELOG.md
git commit -m "Release v0.2.0 - New features"
git tag v0.2.0

# 4. Build
python -m build

# 5. Upload
twine upload dist/*

# 6. Push
git push origin main --tags
```

### For Major Release (Breaking Changes)

```bash
# 1. Update version
# Edit pyproject.toml: version = "1.0.0"

# 2. Update CHANGELOG.md
# Document breaking changes clearly

# 3. Update README.md if needed
# Document migration guide if applicable

# 4. Commit and tag
git add pyproject.toml cph_imgclassification/__init__.py CHANGELOG.md README.md
git commit -m "Release v1.0.0 - First stable release"
git tag v1.0.0

# 5. Build
python -m build

# 6. Upload
twine upload dist/*

# 7. Push
git push origin main --tags
```

---

## Troubleshooting

### Issue: "403 Forbidden" when uploading

**Solution:**
- Verify you're using `__token__` as username (two underscores)
- Check your API token is correct and starts with `pypi-`
- Ensure token hasn't expired
- Try creating a new token

### Issue: "Package name already taken"

**Solution:**
- Check if package exists: https://pypi.org/project/cph-imgclassification/
- If taken, choose a different name in `pyproject.toml`
- Or contact the owner if it's your package

### Issue: "Invalid distribution format"

**Solution:**
- Ensure you have `build` installed: `pip install build`
- Clean and rebuild: `rm -rf build/ dist/ && python -m build`
- Check `pyproject.toml` syntax is correct

### Issue: "Module not found" after installation

**Solution:**
- Verify package structure is correct
- Check `__init__.py` files exist
- Ensure `pyproject.toml` lists all packages correctly
- Reinstall: `pip uninstall cph-imgclassification && pip install cph-imgclassification`

### Issue: "Command not found" after installation

**Solution:**
- Verify entry point in `pyproject.toml`:
  ```toml
  [project.scripts]
  cph-imgclassification = "cph_imgclassification.__main__:main"
  ```
- Reinstall package: `pip install -e .`
- Check Python scripts directory is in PATH

### Issue: Deprecation warnings during build

**Solution:**
- These are warnings, not errors
- Update `pyproject.toml` to use new format:
  ```toml
  license = "MIT"  # Instead of license = {text = "MIT"}
  ```
- Remove deprecated classifiers

---

## Quick Reference Commands

```bash
# Build package
python -m build

# Install locally (development)
pip install -e .

# Install from local build
pip install dist/cph_imgclassification-*.whl

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Check package info
pip show cph-imgclassification

# Uninstall
pip uninstall cph-imgclassification
```

---

## Additional Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Documentation](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Setuptools Documentation](https://setuptools.pypa.io/)

---

## Notes

- Always test on Test PyPI before production release
- Keep `CHANGELOG.md` updated for each release
- Tag releases in Git for version tracking
- Never commit API tokens or credentials
- Use environment variables for tokens in CI/CD

---

**Last Updated:** 2025-01-24  
**Package Name:** cph-imgclassification  
**Author:** chandra  
**Email:** chandra385123@gmail.com  
**Repository:** https://github.com/imchandra11/cph-imgclassification
