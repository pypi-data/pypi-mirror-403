# PyPI Publishing Guide with OIDC

This guide explains how to set up automatic publishing to PyPI using GitHub Actions with OIDC (Trusted Publishers).

## 🔐 Benefits of OIDC Publishing

- ✅ No API tokens to manage or rotate
- ✅ More secure (no long-lived credentials)
- ✅ Automatic authentication via GitHub Actions
- ✅ Built-in audit trail

## 📋 Setup Instructions

### Step 1: Prepare Your Package

Make sure your `pyproject.toml` has all required metadata:
- `name` - Package name on PyPI
- `version` - Current version
- `description` - Short description
- `authors` - Your information
- `license` - License type

### Step 2: Configure PyPI Trusted Publisher

1. **Go to PyPI** (or TestPyPI for testing)
   - PyPI: https://pypi.org
   - TestPyPI: https://test.pypi.org

2. **Create an account** if you don't have one

3. **Configure Trusted Publisher**:
   - Go to your account settings
   - Navigate to "Publishing" section
   - Click "Add a new pending publisher"
   - Fill in the form:
     ```
     PyPI Project Name: weav-provider-router
     Owner: HungryZhao (your GitHub username)
     Repository name: weav-provider-router-repo
     Workflow name: publish.yml
     Environment name: pypi
     ```

4. **For TestPyPI** (optional, for testing):
   - Repeat above steps on https://test.pypi.org
   - Use environment name: `testpypi`

### Step 3: Create GitHub Environment

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Click **New environment**
4. Name it: `pypi`
5. (Optional) Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (e.g., only `main` or `master`)

6. **(Optional)** Create `testpypi` environment for testing

### Step 4: Create a Release

#### Option A: Create Release via GitHub UI

1. Go to your repository on GitHub
2. Click **Releases** → **Draft a new release**
3. Create a new tag (e.g., `v0.1.0`)
4. Fill in release title and description
5. Click **Publish release**
6. GitHub Actions will automatically build and publish to PyPI

#### Option B: Create Release via Git Command

```bash
# Update version in pyproject.toml first
git add pyproject.toml
git commit -m "Bump version to 0.1.0"

# Create and push tag
git tag v0.1.0
git push origin v0.1.0

# Then create release on GitHub
```

#### Option C: Manual Trigger (for testing)

1. Go to **Actions** tab
2. Select **Publish to PyPI** workflow
3. Click **Run workflow**
4. This will publish to TestPyPI (if configured)

## 📦 Workflow Overview

The publish workflow (`publish.yml`) has three jobs:

### 1. Build Job
- Checks out code
- Sets up Python
- Installs build tools
- Builds wheel and source distribution
- Validates distributions
- Uploads as artifact

### 2. Publish to PyPI Job
- Downloads build artifacts
- Uses OIDC to authenticate with PyPI
- Publishes to PyPI
- **Triggers on**: Release published

### 3. Publish to TestPyPI Job (Optional)
- Downloads build artifacts
- Uses OIDC to authenticate with TestPyPI
- Publishes to TestPyPI
- **Triggers on**: Manual workflow dispatch

## 🔄 Version Management

### Semantic Versioning

Follow semantic versioning (semver):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.1"  # Update this
```

### Pre-release Versions

For alpha/beta/rc releases:
```toml
version = "0.2.0a1"  # alpha
version = "0.2.0b1"  # beta
version = "0.2.0rc1" # release candidate
```

## 🧪 Testing the Release Process

### Test on TestPyPI First

1. Set up TestPyPI trusted publisher (see Step 2)
2. Manually trigger the workflow
3. Check TestPyPI: https://test.pypi.org/project/weav-provider-router/

### Install from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ weav-provider-router
```

## 📝 Release Checklist

Before creating a release:

- [ ] All tests passing
- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] No uncommitted changes
- [ ] PyPI trusted publisher configured
- [ ] GitHub environment created

## 🚨 Troubleshooting

### "Trusted publisher not configured"

**Solution**: Follow Step 2 to configure trusted publisher on PyPI

### "Environment not found"

**Solution**: Create the `pypi` environment in GitHub repo settings

### "Permission denied (id-token)"

**Solution**: The workflow needs `id-token: write` permission (already configured)

### "Package already exists"

**Solution**: You can't re-upload the same version. Bump version number.

### "Invalid distribution"

**Solution**: Run `twine check dist/*` locally to validate package

## 🔍 Monitoring

After publishing:

1. **Check PyPI**: https://pypi.org/project/weav-provider-router/
2. **Check GitHub Actions**: See workflow run logs
3. **Test installation**:
   ```bash
   pip install weav-provider-router
   ```

## 📚 Additional Resources

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)

## 🎯 Quick Commands

```bash
# Build locally
python -m build

# Check package
twine check dist/*

# Test upload to TestPyPI (requires API token)
twine upload --repository testpypi dist/*

# Create git tag
git tag v0.1.0
git push origin v0.1.0
```

## ✨ Automatic Publishing Flow

```
1. Update version in pyproject.toml
2. Commit changes
3. Create GitHub Release with tag (e.g., v0.1.0)
4. GitHub Actions automatically:
   - Builds package
   - Authenticates with PyPI via OIDC
   - Publishes to PyPI
5. Package is live on PyPI!
```

---

**Note**: The first time you publish, you need to manually configure the trusted publisher on PyPI. After that, all future releases are automatic!
