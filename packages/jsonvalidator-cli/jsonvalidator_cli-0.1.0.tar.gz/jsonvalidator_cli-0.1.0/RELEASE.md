# Release Process Guide

This guide explains how to create and publish a release for the JSON Validator CLI project.

## Prerequisites

- Git installed and configured
- GitHub account with push access to the repository
- PyPI account (for package distribution)
- Python 3.7+ installed

## Step 1: Prepare for Release

### Update Version Number

Update the version in the following files:
- `jsonvalidator/__init__.py`
- `setup.py`
- `pyproject.toml`

Example: Change from `0.1.0` to `0.2.0`

### Update CHANGELOG.md

Add a new section for the release with:
- Release version and date
- List of changes under categories: Added, Changed, Fixed, Removed
- Link to the release tag

```markdown
## [0.2.0] - 2026-02-15

### Added
- New feature X

### Fixed
- Bug Y
```

### Run Tests

Ensure all tests pass:
```bash
pytest tests/ -v
```

### Lint Code

Ensure code passes linting:
```bash
flake8 jsonvalidator tests
```

## Step 2: Commit and Push Changes

```bash
git add .
git commit -m "Prepare release v0.2.0"
git push origin main
```

## Step 3: Create a Git Tag

Create an annotated tag for the release:

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

## Step 4: Create GitHub Release

1. Go to your repository on GitHub
2. Click on "Releases" in the right sidebar
3. Click "Draft a new release"
4. Fill in the details:
   - **Tag version**: Select `v0.2.0` (the tag you just created)
   - **Release title**: `v0.2.0 - Brief Description`
   - **Description**: Copy from CHANGELOG.md and add:
     ```markdown
     ## Installation
     
     ```bash
     pip install jsonvalidator-cli==0.2.0
     ```
     
     ## Changes in this release
     [Paste from CHANGELOG]
     ```
5. Click "Publish release"

## Step 5: Build the Package

Clean previous builds:
```bash
rm -rf build/ dist/ *.egg-info
```

Build the distribution:
```bash
python -m pip install --upgrade build
python -m build
```

This creates:
- `dist/jsonvalidator-cli-0.2.0.tar.gz` (source distribution)
- `dist/jsonvalidator_cli-0.2.0-py3-none-any.whl` (wheel distribution)

## Step 6: Upload to PyPI

### Test on TestPyPI (Optional but Recommended)

```bash
python -m pip install --upgrade twine
python -m twine upload --repository testpypi dist/*
```

Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ jsonvalidator-cli
```

### Upload to Production PyPI

```bash
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials.

## Step 7: Verify the Release

1. **GitHub Release**: Check that the release appears on GitHub
2. **PyPI Package**: Visit https://pypi.org/project/jsonvalidator-cli/
3. **Test Installation**: 
   ```bash
   pip install jsonvalidator-cli==0.2.0
   jsonvalidator version
   ```

## Quick Release Checklist

- [ ] Update version numbers in all files
- [ ] Update CHANGELOG.md
- [ ] Run all tests
- [ ] Run linter
- [ ] Commit changes
- [ ] Create and push git tag
- [ ] Create GitHub release
- [ ] Build distribution packages
- [ ] Upload to PyPI
- [ ] Verify installation

## Initial Release (v0.1.0) - Quick Start

For your first release for the assignment:

```bash
# 1. Ensure everything is committed
git add .
git commit -m "Initial release v0.1.0"

# 2. Create and push tag
git tag -a v0.1.0 -m "Initial release - JSON Validator CLI"
git push origin main
git push origin v0.1.0

# 3. Build package
python -m pip install --upgrade build twine
python -m build

# 4. Create GitHub Release (via web interface)
# - Go to GitHub > Releases > Draft a new release
# - Select tag v0.1.0
# - Add title and description from CHANGELOG
# - Publish

# 5. Upload to PyPI (optional for assignment)
python -m twine upload dist/*
```

## Troubleshooting

### Tag already exists
```bash
git tag -d v0.1.0  # Delete local tag
git push origin :refs/tags/v0.1.0  # Delete remote tag
# Then recreate the tag
```

### Build fails
```bash
rm -rf build/ dist/ *.egg-info
pip install --upgrade setuptools wheel build
python -m build
```

### PyPI upload fails
- Check credentials
- Ensure version doesn't already exist on PyPI
- Verify package name is available

## Additional Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Python Packaging Guide](https://packaging.python.org/)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
