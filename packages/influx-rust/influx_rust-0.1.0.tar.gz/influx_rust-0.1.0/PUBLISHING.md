# Publishing influx-rust to PyPI

This guide explains how to publish the influx-rust package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
   - Scope: "Entire account" (for first upload) or "Project: influx-rust" (for updates)
   - Save the token securely - it's shown only once!

## Option 1: Test on TestPyPI First (Recommended)

TestPyPI is a separate instance of PyPI for testing packages before publishing to production.

### Step 1: Create TestPyPI Account
- Register at: https://test.pypi.org/account/register/
- Generate token at: https://test.pypi.org/manage/account/token/

### Step 2: Build the Wheel

```bash
# Activate virtual environment
source .venv/bin/activate

# Build wheel
maturin build --release

# Verify wheel
twine check target/wheels/*.whl
```

### Step 3: Upload to TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi target/wheels/*

# You'll be prompted for:
# Username: __token__
# Password: <paste your TestPyPI token>
```

### Step 4: Test Installation from TestPyPI

```bash
# In a different environment
pip install --index-url https://test.pypi.org/simple/ influx-rust

# Test it works
python -c "from influx_rust import get_influx_data_async; print('✅ Import successful')"
```

## Option 2: Publish Directly to PyPI

### Step 1: Build the Wheel

```bash
source .venv/bin/activate
maturin build --release
twine check target/wheels/*.whl
```

### Step 2: Upload to PyPI

```bash
# Upload to PyPI
twine upload target/wheels/*

# You'll be prompted for:
# Username: __token__
# Password: <paste your PyPI token>
```

### Step 3: Verify Publication

```bash
# Check package page
open https://pypi.org/project/influx-rust/

# Install from PyPI
pip install influx-rust

# Test it works
python -c "from influx_rust import get_influx_data_async; print('✅ Works!')"
```

## Using .pypirc for Easier Authentication

Create `~/.pypirc` to avoid entering credentials each time:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...YOUR_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZw...YOUR_TESTPYPI_TOKEN_HERE
```

**IMPORTANT**: Set proper permissions:
```bash
chmod 600 ~/.pypirc
```

Then upload without prompts:
```bash
twine upload --repository testpypi target/wheels/*  # TestPyPI
twine upload target/wheels/*  # PyPI
```

## Version Updates

To publish a new version:

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # or 0.2.0, 1.0.0, etc.
   ```

2. Rebuild and upload:
   ```bash
   maturin build --release
   twine check target/wheels/*.whl
   twine upload target/wheels/*.whl
   ```

## Troubleshooting

### Error: "File already exists"
- You're trying to upload the same version twice
- PyPI doesn't allow re-uploading the same version
- Increment the version number in `pyproject.toml`

### Error: "Invalid or non-existent authentication"
- Check your token is correct
- Make sure username is `__token__` (not your PyPI username)
- Verify token has proper scope (entire account or project-specific)

### Error: "Package name already exists"
- Someone else owns `influx-rust` on PyPI
- Choose a different name (e.g., `influx-rust-async`, `influxdb-rust-client`)
- Update `name` in `pyproject.toml`

## CI/CD with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install maturin
        run: pip install maturin

      - name: Build wheel
        run: maturin build --release

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          pip install twine
          twine upload target/wheels/*
```

Add `PYPI_API_TOKEN` to GitHub repository secrets:
1. Go to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI token

## Next Steps

After publishing to PyPI, update your services:

1. **Update msw-agua-mar/pyproject.toml**:
   ```toml
   dependencies = [
       "influx-rust>=0.1.0",
       # ... other deps
   ]
   ```

2. **Regenerate requirements.txt**:
   ```bash
   cd msw-agua-mar
   uv export --no-hashes --no-dev -o src/requirements.txt
   ```

3. **Simplify Dockerfile** (no Azure Artifacts needed):
   ```dockerfile
   # Just install from PyPI
   RUN pip install --no-cache-dir -r requirements.txt
   ```

That's it! The package is now publicly available on PyPI.
