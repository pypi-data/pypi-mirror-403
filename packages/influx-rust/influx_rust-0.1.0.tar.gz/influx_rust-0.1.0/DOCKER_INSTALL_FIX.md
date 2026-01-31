# Fixing Docker Installation for influx-rust

## Problem

The wheel you built is for **macOS ARM64**, but Docker needs **Linux x86_64/aarch64** wheels.

```
Your wheel: influx_rust-0.1.0-cp38-abi3-macosx_11_0_arm64.whl
Docker needs: influx_rust-0.1.0-cp38-abi3-linux_x86_64.whl
```

## Solution Options

### Option 1: GitHub Actions (Recommended - Automated Multi-Platform Builds)

Create `.github/workflows/build-wheels.yml`:

```yaml
name: Build and Publish Wheels

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Build wheels
        uses: PyO3/maturin-action@v1
        with:
          command: build
          args: --release --out dist

      - name: Upload wheels
        uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}
          path: dist

  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    needs: [build-wheels]
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')

    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: wheels-*
          merge-multiple: true
          path: dist

      - name: Publish to PyPI
        uses: PyO3/maturin-action@v1
        env:
          MATURIN_PYPI_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
        with:
          command: upload
          args: --skip-existing dist/*
```

**How to use:**
1. Save this file
2. Add `PYPI_API_TOKEN` to GitHub repository secrets
3. Create a git tag: `git tag v0.1.0 && git push origin v0.1.0`
4. GitHub Actions will build for Linux + macOS and publish to PyPI

**Pros:**
- ✅ Builds for multiple platforms automatically
- ✅ Automated publishing on tags
- ✅ Free for public repositories

---

### Option 2: Build from Source in Docker (Simplest for Now)

Update your `msw-agua-mar/Dockerfile` to build from source:

```dockerfile
FROM python:3.12-slim

RUN pip install -U pip

WORKDIR /src

# Install Rust and build dependencies for influx-rust
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Install maturin
RUN pip install maturin

# Copy requirements and install Python dependencies
ADD ./src/requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

# Security hardening
RUN chmod -R 100 *
RUN apt-get -s remove apt
RUN rm -R /bin/cat /bin/ls /bin/pwd /bin/ln /bin/mv /bin/cp
RUN rm -Rf /var/cache/apt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Pros:**
- ✅ Works immediately
- ✅ No need to build wheels separately

**Cons:**
- ❌ Slow Docker builds (~5-10 minutes)
- ❌ Large Docker image size

---

### Option 3: Upload Linux Wheel from CI/CD (Azure Pipelines)

Update your `influx-rust/azure-pipeline.yml` to build Linux wheels:

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: ubuntu-latest  # This is Linux!

variables:
  packageName: 'influx-rust'
  packageVersion: '0.1.0'

stages:
  - stage: Build
    displayName: 'Build Rust Wheel'
    jobs:
      - job: BuildWheel
        displayName: 'Build and Publish Wheel'
        steps:
          # Install Rust
          - script: |
              curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
              source $HOME/.cargo/env
              rustup default stable
            displayName: 'Install Rust toolchain'

          # Install maturin and build
          - script: |
              source $HOME/.cargo/env
              pip install maturin twine
              maturin build --release
              ls -lh target/wheels/
            displayName: 'Build Python wheel'

          # Upload to PyPI
          - script: |
              source $HOME/.cargo/env
              python -m twine upload target/wheels/*.whl
            env:
              TWINE_USERNAME: __token__
              TWINE_PASSWORD: $(PYPI_API_TOKEN)
            displayName: 'Upload wheel to PyPI'
```

**Setup:**
1. Add `PYPI_API_TOKEN` to Azure Pipeline variables
2. Push to main branch
3. Azure will build **Linux** wheel and publish to PyPI

**Pros:**
- ✅ Builds Linux wheels automatically
- ✅ Uses existing Azure infrastructure

---

## Quick Fix for Today (Option 2)

The fastest solution right now is to **build from source in Docker**. Let me update your Dockerfile:
