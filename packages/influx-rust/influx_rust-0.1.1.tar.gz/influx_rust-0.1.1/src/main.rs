use anyhow::Result;
use influxdb2::models::Query;
use influxdb2::Client;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::env;
use std::time::Instant;

#[tokio::main]
async fn main() -> Result<()> {
    // Parse command-line arguments
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: {} <flux_query> [--url URL] [--token TOKEN] [--org ORG]", args[0]);
        eprintln!("\nExample:");
        eprintln!("  {} 'from(bucket: \"my-bucket\") |> range(start: -1h)' --url http://localhost:8086 --token mytoken --org myorg", args[0]);
        eprintln!("\nOr use environment variables:");
        eprintln!("  INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG");
        std::process::exit(1);
    }

    let query_str = &args[1];

    // Get connection parameters from args or environment
    let url = get_arg_or_env(&args, "--url", "INFLUXDB_URL")
        .unwrap_or_else(|| "http://localhost:8086".to_string());
    let token = get_arg_or_env(&args, "--token", "INFLUXDB_TOKEN")
        .expect("InfluxDB token required (--token or INFLUXDB_TOKEN env var)");
    let org = get_arg_or_env(&args, "--org", "INFLUXDB_ORG")
        .expect("InfluxDB org required (--org or INFLUXDB_ORG env var)");

    println!("=== InfluxDB Rust POC ===");
    println!("URL: {}", url);
    println!("Org: {}", org);
    println!("Query: {}\n", query_str);

    // Execute query with performance measurements
    match get_influx_data_async(&url, &token, &org, query_str).await {
        Ok(results) => {
            println!("\n=== Results ===");
            println!("Total records: {}", results.len());
            println!("\nFirst 3 records (sample):");
            for (i, record) in results.iter().take(3).enumerate() {
                println!("{}: {}", i + 1, serde_json::to_string_pretty(record)?);
            }
        }
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    }

    Ok(())
}

async fn get_influx_data_async(
    url: &str,
    token: &str,
    org: &str,
    query_str: &str,
) -> Result<Vec<HashMap<String, Value>>> {
    let start_total = Instant::now();

    // Step 1: Initialize client connection
    let start_step = Instant::now();
    let client = Client::new(url, org, token);
    let time_client_init = start_step.elapsed();
    println!(
        "[PERF][InfluxDB] Client initialization: {:.4}s",
        time_client_init.as_secs_f64()
    );

    // Step 2: Execute query and get raw FluxRecords
    let start_step = Instant::now();
    let query = Query::new(query_str.to_string());

    // Use query_raw to get Vec<FluxRecord>
    let records = client.query_raw(Some(query)).await?;

    let time_query = start_step.elapsed();
    println!(
        "[PERF][InfluxDB] Query execution: {:.4}s",
        time_query.as_secs_f64()
    );

    // Step 3: Convert FluxRecords to HashMap
    let start_step = Instant::now();

    let results: Vec<HashMap<String, Value>> = records
        .into_iter()
        .map(|record| {
            let mut map = HashMap::new();

            // Convert each field in the FluxRecord to JSON Value
            for (key, value) in record.values {
                let json_value = convert_influx_value_to_json(value);
                map.insert(key, json_value);
            }

            map
        })
        .collect();

    let time_process = start_step.elapsed();
    println!(
        "[PERF][InfluxDB] Process records: {:.4}s",
        time_process.as_secs_f64()
    );

    let time_total = start_total.elapsed();
    println!(
        "[PERF][InfluxDB] TOTAL InfluxDB operation: {:.4}s",
        time_total.as_secs_f64()
    );
    println!("[PERF][InfluxDB] Records returned: {}", results.len());

    Ok(results)
}

fn convert_influx_value_to_json(value: influxdb2_structmap::value::Value) -> Value {
    use influxdb2_structmap::value::Value as InfluxValue;

    match value {
        InfluxValue::String(s) => json!(s),
        InfluxValue::Double(f) => json!(*f),
        InfluxValue::Bool(b) => json!(b),
        InfluxValue::Long(i) => json!(i),
        InfluxValue::UnsignedLong(u) => json!(u),
        InfluxValue::Duration(d) => json!(d),
        InfluxValue::Base64Binary(b) => json!(b),
        InfluxValue::TimeRFC(t) => json!(t),
        InfluxValue::Unknown => Value::Null,
    }
}

fn get_arg_or_env(args: &[String], flag: &str, env_var: &str) -> Option<String> {
    // Check command-line arguments first
    for i in 0..args.len() {
        if args[i] == flag && i + 1 < args.len() {
            return Some(args[i + 1].clone());
        }
    }
    // Fall back to environment variable
    env::var(env_var).ok()
}
