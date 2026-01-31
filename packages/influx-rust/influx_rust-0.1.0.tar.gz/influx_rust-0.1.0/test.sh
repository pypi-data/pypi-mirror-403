#!/bin/bash

# Test script for InfluxDB Rust POC
# Make sure to set your environment variables first:
# export INFLUXDB_URL="your-url"
# export INFLUXDB_TOKEN="your-token"
# export INFLUXDB_ORG="your-org"

# Example query - list all buckets
QUERY="buckets()"

echo "Testing InfluxDB Rust POC..."
echo "Query: $QUERY"
echo ""

./target/release/influx-rust "$QUERY"
