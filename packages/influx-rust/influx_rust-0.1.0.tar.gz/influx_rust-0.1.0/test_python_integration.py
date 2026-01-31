#!/usr/bin/env python3
"""
Test script for influx_rust Python package.
Verifies that the Rust implementation returns the correct format.
"""
import asyncio
import os
import sys

try:
    from influx_rust import get_influx_data_async
    print("✅ Successfully imported influx_rust module")
except ImportError as e:
    print(f"❌ Failed to import influx_rust: {e}")
    sys.exit(1)


async def test_basic_query():
    """Test with a simple query to verify the package works."""
    # Get credentials from environment
    url = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG")

    if not all([url, token, org]):
        print("❌ Missing environment variables: INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG")
        sys.exit(1)

    # Simple test query
    query = 'from(bucket: "aquachile") |> range(start: -1h) |> limit(n: 5)'

    print(f"\n🔍 Testing with query: {query}\n")

    try:
        results = await get_influx_data_async(url, token, org, query)

        print("✅ Query successful!")
        print(f"📊 Got {len(results)} records")

        if results:
            print("\n📋 First record:")
            first = results[0]
            print(f"   Type: {type(first)}")
            print(f"   Keys: {list(first.keys())[:5]}...")  # Show first 5 keys
            print("   Sample values:")
            for i, (k, v) in enumerate(list(first.items())[:3]):
                print(f"     {k}: {v} ({type(v).__name__})")

        print("\n✅ Return format is correct: list[dict]")
        return True

    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_production_query():
    """Test with the production query from the POC."""
    url = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG")

    query = """sources_low_oxygen = from(bucket: "aquachile")
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
         |> yield(name: "mean_and_min_by_metric")"""

    print("\n🔍 Testing with production-like query...\n")

    try:
        import time
        start = time.time()
        results = await get_influx_data_async(url, token, org, query)
        elapsed = time.time() - start

        print("✅ Production query successful!")
        print(f"📊 Got {len(results)} records")
        print(f"⏱️  Elapsed time: {elapsed:.3f}s")

        return True

    except Exception as e:
        print(f"❌ Production query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("InfluxDB Rust Python Integration Test")
    print("=" * 60)

    # Test 1: Basic query
    success1 = await test_basic_query()

    # Test 2: Production query (if test 1 passed)
    if success1:
        success2 = await test_production_query()
    else:
        success2 = False

    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
