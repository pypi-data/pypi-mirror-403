#!/bin/bash

# Performance comparison script between Python and Rust implementations
#
# Usage:
#   ./compare_performance.sh "<your_flux_query>" "<python_service_path>"
#
# Example:
#   ./compare_performance.sh 'from(bucket: "agua_mar") |> range(start: -1h) |> limit(n: 100)' "../msw-agua-mar"


# Complex production query - using heredoc to preserve all quotes correctly
read -r -d '' QUERY << 'EOF'
sources_low_oxygen = from(bucket: "aquachile")
    |> range(start: 2026-01-14T00:00:00Z, stop: 2026-01-28T00:00:00Z)
    |> filter(fn: (r) => r._measurement == "aguamar_variables" and
        (
        r._field == "o2_disuelto_5_metros"
        or r._field == "o2_disuelto_10_metros"
        )
        and (r.source == "AM-ac-puntapaula-jen_innovex" or r.source == "AM-ac-canutillar_innovex" or r.source == "AM-ac-pangue_innovex" or r.source == "AM-ac-teguel3-inyeccion_innovex" or r.source == "AM-ac-abtao-jen_innovex" or r.source == "AM-ac-detif_innovex" or r.source == "AM-ac-huenquillahue_innovex" or r.source == "AM-ac-herradura_innovex" or r.source == "AM-ac-cahueldao-inyeccion_innovex" or r.source == "AM-ac-quiquel2_innovex" or r.source == "AM-ac-huelmo_innovex" or r.source == "AM-ac-puntapaula_innovex" or r.source == "innovasea-Huenquillahue_innovex" or r.source == "AM-ac-yutuy_innovex" or r.source == "AM-ac-quilquesur-jen_innovex" or r.source == "AM-ac-guar_innovex" or r.source == "AM-ac-teguel3_innovex" or r.source == "AM-ac-tauco-inyeccion_innovex" or r.source == "AM-ac-chauques-inyeccion_innovex" or r.source == "AM-ac-ichuac-inyeccion_innovex" or r.source == "AM-ac-chidhuapi-inyeccion_innovex" or r.source == "AM-ac-teguel2_innovex" or r.source == "AM-ac-pangue-inyeccion_innovex" or r.source == "AM-ac-puntapelu_innovex" or r.source == "AM-ac-ichuac_innovex" or r.source == "AM-ac-lille2_innovex" or r.source == "AM-ac-yatac_innovex" or r.source == "AM-ac-serapio-inyeccion_innovex" or r.source == "AM-ac-chauques_innovex" or r.source == "AM-ac-yutuy-inyeccion_innovex" or r.source == "AM-ac-cahueldao_innovex" or r.source == "AM-ac-capera_innovex" or r.source == "AM-ac-sanpedro_innovex" or r.source == "AM-ac-quetalco-inyeccion_innovex" or r.source == "innovasea-Capera_innovex" or r.source == "AM-ac-puqueldon_innovex" or r.source == "AM-ac-serapio_innovex" or r.source == "AM-ac-quetalco_innovex" or r.source == "AM-ac-chidhuapi_innovex" or r.source == "AM-ac-sotomo_innovex" or r.source == "AM-ac-quiquel2-inyeccion_innovex" or r.source == "AM-ac-detif-jen_innovex" or r.source == "AM-ac-tauco_innovex")
        and r._value < 5
    )
    |> group(columns: ["_field", "source"])
    |> first()

min_query = from(bucket: "aquachile")
    |> range(start: 2026-01-14T00:00:00Z, stop: 2026-01-28T00:00:00Z)
    |> filter(fn: (r) => r._measurement == "aguamar_variables" and
        (
        r._field == "o2_disuelto_5_metros"
        or r._field == "o2_disuelto_10_metros"
        )
        and (r.source == "AM-ac-puntapaula-jen_innovex" or r.source == "AM-ac-canutillar_innovex" or r.source == "AM-ac-pangue_innovex" or r.source == "AM-ac-teguel3-inyeccion_innovex" or r.source == "AM-ac-abtao-jen_innovex" or r.source == "AM-ac-detif_innovex" or r.source == "AM-ac-huenquillahue_innovex" or r.source == "AM-ac-herradura_innovex" or r.source == "AM-ac-cahueldao-inyeccion_innovex" or r.source == "AM-ac-quiquel2_innovex" or r.source == "AM-ac-huelmo_innovex" or r.source == "AM-ac-puntapaula_innovex" or r.source == "innovasea-Huenquillahue_innovex" or r.source == "AM-ac-yutuy_innovex" or r.source == "AM-ac-quilquesur-jen_innovex" or r.source == "AM-ac-guar_innovex" or r.source == "AM-ac-teguel3_innovex" or r.source == "AM-ac-tauco-inyeccion_innovex" or r.source == "AM-ac-chauques-inyeccion_innovex" or r.source == "AM-ac-ichuac-inyeccion_innovex" or r.source == "AM-ac-chidhuapi-inyeccion_innovex" or r.source == "AM-ac-teguel2_innovex" or r.source == "AM-ac-pangue-inyeccion_innovex" or r.source == "AM-ac-puntapelu_innovex" or r.source == "AM-ac-ichuac_innovex" or r.source == "AM-ac-lille2_innovex" or r.source == "AM-ac-yatac_innovex" or r.source == "AM-ac-serapio-inyeccion_innovex" or r.source == "AM-ac-chauques_innovex" or r.source == "AM-ac-yutuy-inyeccion_innovex" or r.source == "AM-ac-cahueldao_innovex" or r.source == "AM-ac-capera_innovex" or r.source == "AM-ac-sanpedro_innovex" or r.source == "AM-ac-quetalco-inyeccion_innovex" or r.source == "innovasea-Capera_innovex" or r.source == "AM-ac-puqueldon_innovex" or r.source == "AM-ac-serapio_innovex" or r.source == "AM-ac-quetalco_innovex" or r.source == "AM-ac-chidhuapi_innovex" or r.source == "AM-ac-sotomo_innovex" or r.source == "AM-ac-quiquel2-inyeccion_innovex" or r.source == "AM-ac-detif-jen_innovex" or r.source == "AM-ac-tauco_innovex")
    )
    |> group(columns: ["_field", "source"])
    |> min()

mean_query = from(bucket: "aquachile")
    |> range(start: 2026-01-14T00:00:00Z, stop: 2026-01-28T00:00:00Z)
    |> filter(fn: (r) => r._measurement == "aguamar_variables" and
        (
        r._field == "o2_disuelto_5_metros"
        or r._field == "o2_disuelto_10_metros"
        )
        and (r.source == "AM-ac-puntapaula-jen_innovex" or r.source == "AM-ac-canutillar_innovex" or r.source == "AM-ac-pangue_innovex" or r.source == "AM-ac-teguel3-inyeccion_innovex" or r.source == "AM-ac-abtao-jen_innovex" or r.source == "AM-ac-detif_innovex" or r.source == "AM-ac-huenquillahue_innovex" or r.source == "AM-ac-herradura_innovex" or r.source == "AM-ac-cahueldao-inyeccion_innovex" or r.source == "AM-ac-quiquel2_innovex" or r.source == "AM-ac-huelmo_innovex" or r.source == "AM-ac-puntapaula_innovex" or r.source == "innovasea-Huenquillahue_innovex" or r.source == "AM-ac-yutuy_innovex" or r.source == "AM-ac-quilquesur-jen_innovex" or r.source == "AM-ac-guar_innovex" or r.source == "AM-ac-teguel3_innovex" or r.source == "AM-ac-tauco-inyeccion_innovex" or r.source == "AM-ac-chauques-inyeccion_innovex" or r.source == "AM-ac-ichuac-inyeccion_innovex" or r.source == "AM-ac-chidhuapi-inyeccion_innovex" or r.source == "AM-ac-teguel2_innovex" or r.source == "AM-ac-pangue-inyeccion_innovex" or r.source == "AM-ac-puntapelu_innovex" or r.source == "AM-ac-ichuac_innovex" or r.source == "AM-ac-lille2_innovex" or r.source == "AM-ac-yatac_innovex" or r.source == "AM-ac-serapio-inyeccion_innovex" or r.source == "AM-ac-chauques_innovex" or r.source == "AM-ac-yutuy-inyeccion_innovex" or r.source == "AM-ac-cahueldao_innovex" or r.source == "AM-ac-capera_innovex" or r.source == "AM-ac-sanpedro_innovex" or r.source == "AM-ac-quetalco-inyeccion_innovex" or r.source == "innovasea-Capera_innovex" or r.source == "AM-ac-puqueldon_innovex" or r.source == "AM-ac-serapio_innovex" or r.source == "AM-ac-quetalco_innovex" or r.source == "AM-ac-chidhuapi_innovex" or r.source == "AM-ac-sotomo_innovex" or r.source == "AM-ac-quiquel2-inyeccion_innovex" or r.source == "AM-ac-detif-jen_innovex" or r.source == "AM-ac-tauco_innovex")
    )
    |> group(columns: ["_field", "idta", "source"])
    |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)

first_join = join(tables: {source: sources_low_oxygen, mean: mean_query}, on: ["_field", "source"])

join(tables: {mean: first_join, min: min_query}, on: ["_field", "source"])
    |> yield(name: "mean_and_min_by_metric")
EOF

PYTHON_SERVICE_PATH="${2:-../msw-agua-mar}"

echo "=========================================="
echo "PERFORMANCE COMPARISON: Python vs Rust"
echo "=========================================="
echo ""
echo "Query: $QUERY"
echo ""

# Check if environment variables are set
if [ -z "$INFLUXDB_URL" ] || [ -z "$INFLUXDB_TOKEN" ] || [ -z "$INFLUXDB_ORG" ]; then
    echo "ERROR: Please set environment variables:"
    echo "  export INFLUXDB_URL=\"your-url\""
    echo "  export INFLUXDB_TOKEN=\"your-token\""
    echo "  export INFLUXDB_ORG=\"your-org\""
    exit 1
fi

# Run Rust version
echo "===================="
echo "  RUST VERSION"
echo "===================="
echo ""
time ./target/release/influx-rust-poc "$QUERY" 2>&1

echo ""
echo ""
echo "===================="
echo "  PYTHON VERSION"
echo "===================="
echo ""

# Create a temporary Python script to test the Python implementation
cat > /tmp/test_influx_python.py <<EOF
import sys
import os
import asyncio

# Add the service path to sys.path
sys.path.insert(0, "$PYTHON_SERVICE_PATH/src")

from app.database.influxdb import get_influx_data_async

async def main():
    query = """$QUERY"""
    results = await get_influx_data_async(query)
    print(f"\\nTotal records returned: {len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run Python version (requires the service's dependencies to be installed)
time python3 /tmp/test_influx_python.py 2>&1

echo ""
echo "=========================================="
echo "Comparison complete!"
echo "=========================================="
echo ""
echo "NOTE: Look at the TOTAL InfluxDB operation times to compare."
echo "Expected improvement in Rust:"
echo "  - No JSON serialization/deserialization overhead"
echo "  - Faster record processing"
echo "  - Lower memory usage"
