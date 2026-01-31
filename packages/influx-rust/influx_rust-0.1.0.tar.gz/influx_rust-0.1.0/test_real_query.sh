#!/bin/bash

# Test with real production query
# This query tests oxygen levels across multiple sources and performs aggregations

echo "=========================================="
echo "InfluxDB Rust POC - Real Query Test"
echo "=========================================="
echo ""

# Check environment variables
if [ -z "$INFLUXDB_URL" ] || [ -z "$INFLUXDB_TOKEN" ] || [ -z "$INFLUXDB_ORG" ]; then
    echo "ERROR: Please set environment variables:"
    echo "  export INFLUXDB_URL=\"your-url\""
    echo "  export INFLUXDB_TOKEN=\"your-token\""
    echo "  export INFLUXDB_ORG=\"your-org\""
    exit 1
fi

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

echo "Running Rust implementation..."
echo ""

time ./target/release/influx-rust "$QUERY"

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="
echo ""
echo "This query performs:"
echo "  - 3 separate InfluxDB queries (sources_low_oxygen, min_query, mean_query)"
echo "  - Filtering across 40+ sources"
echo "  - 2 joins"
echo "  - Aggregations (first, min, mean)"
echo "  - Time window aggregation (30m)"
echo ""
echo "Check the [PERF][InfluxDB] lines above for timing breakdown."
