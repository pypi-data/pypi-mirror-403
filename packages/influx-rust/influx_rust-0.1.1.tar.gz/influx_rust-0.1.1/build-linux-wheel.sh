#!/bin/bash
# Build Linux wheel for influx-rust using Docker

set -e

echo "🐋 Building Linux wheel for influx-rust..."

# Build the builder image
echo "📦 Building Docker image..."
docker build -f Dockerfile.builder -t influx-rust-builder .

# Run the build
echo "🏗️  Building wheel..."
docker run --rm -v "$(pwd)":/io influx-rust-builder

echo ""
echo "✅ Linux wheel built successfully!"
echo "📂 Wheel location: target/wheels/"
ls -lh target/wheels/*.whl
