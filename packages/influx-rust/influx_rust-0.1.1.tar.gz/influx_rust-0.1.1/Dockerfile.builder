# Dockerfile for building Linux wheels for influx-rust
FROM rust:1.93-slim

# Install Python and build tools
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Install maturin
RUN pip3 install --break-system-packages maturin

WORKDIR /io

# Copy project files
COPY . .

# Build the wheel
CMD ["maturin", "build", "--release", "--strip"]
