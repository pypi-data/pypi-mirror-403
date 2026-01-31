# influx-rust

High-performance InfluxDB query library for Python, powered by Rust.

[![PyPI version](https://img.shields.io/pypi/v/influx-rust.svg)](https://pypi.org/project/influx-rust/)
[![Python versions](https://img.shields.io/pypi/pyversions/influx-rust.svg)](https://pypi.org/project/influx-rust/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why influx-rust?

**10x faster** InfluxDB queries compared to native Python implementations. By leveraging Rust's performance with PyO3 bindings, `influx-rust` eliminates JSON serialization overhead and interpreter bottlenecks while maintaining a familiar Python API.

### Performance Comparison

| Implementation | Query Time (40+ sources, 24h range) | Improvement |
|----------------|-------------------------------------|-------------|
| **Python (influxdb-client)** | ~38-40 seconds | baseline |
| **influx-rust** | ~3-4 seconds | **10x faster** ✅ |

Real-world performance measured on production queries with 40+ data sources, aggregations, and time-windowed data.

## Features

- 🚀 **10x faster** than Python native InfluxDB clients
- 🔄 **Drop-in replacement** for existing `influxdb-client` async queries
- 🦀 **Rust-powered** performance with zero-copy deserialization
- 🐍 **Python-friendly** async/await interface
- 📦 **Pre-built wheels** for Linux, macOS, and Windows
- 🔒 **Type-safe** Rust implementation with comprehensive error handling
- ⚡ **Tokio async runtime** for concurrent query execution

## Installation

```bash
pip install influx-rust
```

Requires Python 3.8 or higher.

## Quick Start

```python
from influx_rust import get_influx_data_async

# Same interface as your existing code
results = await get_influx_data_async(
    url="https://your-influxdb.com",
    token="your-token",
    org="your-org",
    query='''
        from(bucket: "sensors")
        |> range(start: -24h)
        |> filter(fn: (r) => r._measurement == "temperature")
        |> aggregateWindow(every: 30m, fn: mean)
    '''
)

# Returns list of dictionaries
for record in results:
    print(record)  # {'_time': '2024-01-29T10:00:00Z', '_value': 23.5, ...}
```

## Usage Examples

### Basic Query

```python
import asyncio
from influx_rust import get_influx_data_async

async def fetch_temperature_data():
    data = await get_influx_data_async(
        url="https://influx.example.com",
        token="your_token_here",
        org="my_org",
        query='from(bucket: "sensors") |> range(start: -1h)'
    )
    return data

# Run the async function
results = asyncio.run(fetch_temperature_data())
print(f"Retrieved {len(results)} records")
```

### Complex Query with Aggregations

```python
# Multi-source query with joins and aggregations
query = '''
from(bucket: "agua_mar")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "oxygen")
  |> filter(fn: (r) => contains(value: r.source, set: ["sensor1", "sensor2", "sensor3"]))
  |> aggregateWindow(every: 30m, fn: mean)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

data = await get_influx_data_async(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG,
    query=query
)
```

### Integration with Existing Python Code

Drop-in replacement for `influxdb-client`:

```python
# BEFORE: Using influxdb-client (slow)
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

async def get_data_old_way():
    client = InfluxDBClient(url=url, token=token, org=org)
    query_api = client.query_api()
    tables = query_api.query(query)
    # ... process tables ...

# AFTER: Using influx-rust (fast)
from influx_rust import get_influx_data_async

async def get_data_new_way():
    # Same result, 10x faster
    results = await get_influx_data_async(
        url=url,
        token=token,
        org=org,
        query=query
    )
    return results
```

### Error Handling

```python
from influx_rust import get_influx_data_async

try:
    data = await get_influx_data_async(
        url="https://influx.example.com",
        token="invalid_token",
        org="my_org",
        query="from(bucket: 'test') |> range(start: -1h)"
    )
except Exception as e:
    print(f"Query failed: {e}")
    # Handle authentication errors, network issues, etc.
```

## How It Works

`influx-rust` uses [PyO3](https://github.com/PyO3/pyo3) to create Python bindings for a high-performance Rust implementation:

1. **Rust Core**: Uses the official [influxdb2](https://crates.io/crates/influxdb2) Rust client
2. **Zero-Copy Deserialization**: Directly processes InfluxDB responses without intermediate JSON strings
3. **Async Runtime**: Powered by [Tokio](https://tokio.rs/) for efficient concurrent operations
4. **Python Bindings**: PyO3 exposes Rust functions as native Python async functions

### Why It's Faster

| Bottleneck | Python (influxdb-client) | influx-rust |
|------------|-------------------------|-------------|
| **JSON serialization** | ❌ Double serialization (InfluxDB → JSON → Python) | ✅ Zero-copy deserialization |
| **Interpreter overhead** | ❌ Python GIL and interpreter | ✅ Compiled Rust (no GIL) |
| **Memory allocations** | ❌ Intermediate string buffers | ✅ Direct struct mapping |
| **Async runtime** | ❌ Python asyncio | ✅ Tokio (native threads) |

## Development

### Building from Source

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone repository
git clone https://github.com/your-org/influx-rust.git
cd influx-rust

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install maturin
pip install maturin

# Build and install in development mode
maturin develop --release
```

### Running Tests

```bash
# Build release version
cargo build --release

# Run Rust tests
cargo test

# Test Python integration
python -c "from influx_rust import get_influx_data_async; print('✅ Import successful')"
```

### Performance Testing

Compare performance with Python implementation:

```bash
# Set environment variables
export INFLUXDB_URL="https://your-influxdb.com"
export INFLUXDB_TOKEN="your-token"
export INFLUXDB_ORG="your-org"

# Run comparison script
./compare_performance.sh
```

## API Reference

### `get_influx_data_async`

```python
async def get_influx_data_async(
    url: str,
    token: str,
    org: str,
    query: str
) -> list[dict[str, str]]
```

Execute an InfluxDB Flux query asynchronously.

**Parameters:**
- `url` (str): InfluxDB server URL (e.g., `https://influx.example.com`)
- `token` (str): Authentication token
- `org` (str): Organization name
- `query` (str): Flux query string

**Returns:**
- `list[dict[str, str]]`: List of records as dictionaries. Each dictionary contains InfluxDB fields like `_time`, `_value`, `_measurement`, etc.

**Raises:**
- `Exception`: On authentication errors, network failures, or invalid queries

## Requirements

- **Python**: 3.8 or higher
- **Operating Systems**: Linux (x86_64, aarch64), macOS (x86_64, arm64), Windows (x86_64)

Pre-built wheels are available for all supported platforms. No Rust toolchain required for installation.

## Deployment

### Docker

When using in Docker, simply install from PyPI:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

# influx-rust installs from pre-built wheel (no Rust needed!)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "app.py"]
```

No need to install Rust in your Docker container!

### Production Considerations

- **Connection Pooling**: influx-rust reuses connections internally
- **Timeout**: Default timeout is 30 seconds (configurable in future versions)
- **Memory**: Significantly lower memory usage vs Python client (no intermediate buffers)
- **Logging**: Enable debug logs with `RUST_LOG=debug` environment variable

## Roadmap

- [ ] Configurable timeouts
- [ ] Connection pooling configuration
- [ ] Write API support (currently read-only)
- [ ] Streaming queries for large datasets
- [ ] Custom error types instead of generic exceptions
- [ ] Sync version of the API (non-async)

## Benchmarks

Real-world production query (AquaChile agua_mar monitoring):

```bash
Query: 40+ sensors, 24h range, aggregations, joins
Records: ~12,450 records

Python (influxdb-client):
  ⏱️  Query execution: 38.2s
  📊 Memory usage: ~450MB

influx-rust:
  ⏱️  Query execution: 3.8s  (10x faster)
  📊 Memory usage: ~180MB  (2.5x less)
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with:
- [PyO3](https://github.com/PyO3/pyo3) - Rust bindings for Python
- [influxdb2](https://crates.io/crates/influxdb2) - Official InfluxDB Rust client
- [Tokio](https://tokio.rs/) - Async runtime for Rust
- [Maturin](https://github.com/PyO3/maturin) - Build and publish Rust-based Python packages

Developed by AquaChile DevOps for high-performance aquaculture monitoring.

## Support

- 📫 Issues: [GitHub Issues](https://github.com/your-org/influx-rust/issues)
- 📖 Documentation: [GitHub Wiki](https://github.com/your-org/influx-rust/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/influx-rust/discussions)
