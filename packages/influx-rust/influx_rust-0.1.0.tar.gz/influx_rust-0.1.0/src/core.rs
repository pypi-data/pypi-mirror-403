use anyhow::Result;
use influxdb2::models::Query;
use influxdb2::Client;
use serde_json::Value;
use std::collections::HashMap;

/// Core InfluxDB query function (no prints, clean interface)
pub async fn query_influx(
    url: &str,
    token: &str,
    org: &str,
    query_str: &str,
) -> Result<Vec<HashMap<String, Value>>> {
    // Initialize client
    let client = Client::new(url, org, token);

    // Execute query
    let query = Query::new(query_str.to_string());
    let records = client.query_raw(Some(query)).await?;

    // Convert to HashMap
    let results: Vec<HashMap<String, Value>> = records
        .into_iter()
        .map(|record| {
            let mut map = HashMap::new();
            for (key, value) in record.values {
                let json_value = convert_influx_value_to_json(value);
                map.insert(key, json_value);
            }
            map
        })
        .collect();

    Ok(results)
}

fn convert_influx_value_to_json(value: influxdb2_structmap::value::Value) -> Value {
    use influxdb2_structmap::value::Value as InfluxValue;
    use serde_json::json;

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
