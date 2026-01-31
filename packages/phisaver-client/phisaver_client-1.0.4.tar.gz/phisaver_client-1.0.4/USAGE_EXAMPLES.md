# PhiSaver Client Usage Examples

## Authentication

```python
from phisaver_client import get_client_from_env, get_client

# Option 1: Use environment variables
# Set PHISAVER_URL, PHISAVER_USERNAME, PHISAVER_PASSWORD
client = get_client_from_env()

# Option 2: Pass credentials explicitly
client = get_client(
    base_url="https://app.phisaver.com",
    username="your-email@example.com",
    password="your-password"
)
```

## Time Series Data

### Method 1: Dict-like Access (Recommended)

The response models support `__getitem__`, so you can use them like dictionaries:

```python
from phisaver_client.api.ts import ts_series_retrieve

# Fetch time series data
result = ts_series_retrieve.sync(
    client=client,
    bin_="1h",           # 1-hour bins
    sites="demo1",       # Device ID
    start=start_time,
    stop=end_time,
)

# Direct dict-like access (NO .additional_properties needed!)
production_data = result["demo1"]["Production"]
net_data = result["demo1"]["Net"]

for timestamp, value in production_data:
    print(f"Production at {timestamp}: {value}W")
```

### Method 2: Using as_dict() Helper

For explicit conversion to plain dict:

```python
from phisaver_client import as_dict
from phisaver_client.api.ts import ts_series_retrieve

result = ts_series_retrieve.sync(
    client=client,
    bin_="1h",
    sites="demo1,demo2",  # Multiple devices
)

# Convert to plain dict
data = as_dict(result)

# Iterate over all devices and metrics
for device_id, metrics in data.items():
    print(f"Device: {device_id}")
    for metric_name, timeseries in metrics.items():
        print(f"  {metric_name}: {len(timeseries)} data points")
        # Each timeseries is a list of [timestamp, value] pairs
```

### Method 3: With Type Hints

```python
from phisaver_client import TimeSeriesData
from phisaver_client.api.ts import ts_series_retrieve

def process_energy_data(client, site: str) -> TimeSeriesData:
    """Fetch and return time series data with proper typing"""
    result = ts_series_retrieve.sync(
        client=client,
        bin_="15min",
        sites=site,
        attribute="power",
        units="kW",
    )
    
    # Type hints available for IDE autocomplete
    data: TimeSeriesData = as_dict(result)
    return data

# Usage
data = process_energy_data(client, "demo1")
production = data["demo1"]["Production"]  # Full IDE support
```

## Query Parameters

Common parameters for time series queries:

```python
from datetime import datetime, timedelta
from phisaver_client.api.ts import ts_series_retrieve

end = datetime.now()
start = end - timedelta(days=7)

result = ts_series_retrieve.sync(
    client=client,
    bin_="1h",                    # Aggregation interval
    sites="demo1,demo2",          # Comma-separated device IDs
    start=start,                  # Start time
    stop=end,                     # End time
    attribute="power",            # Metric type
    function="mean",              # Aggregation function
    units="kW",                   # Units
    named=True,                   # Use device names instead of IDs
    timeformat="iso",             # Timestamp format (iso/epoch/epochms)
)
```

## Error Handling

```python
from phisaver_client.api.ts import ts_series_retrieve
import httpx

try:
    result = ts_series_retrieve.sync_detailed(  # Use sync_detailed for status code
        client=client,
        bin_="1h",
        sites="demo1",
    )
    
    if result.status_code == 200:
        data = result.parsed
        print(f"Success! Got data for {len(data)} devices")
    else:
        print(f"Error: {result.status_code}")
        
except httpx.TimeoutException:
    print("Request timed out")
except Exception as e:
    print(f"Error: {e}")
```

## Device Management

```python
from phisaver_client.api.devices import devices_list

# List all devices
devices = devices_list.sync(client=client)

for device in devices:
    print(f"{device.ref}: {device.name}")
```

## Best Practices

1. **Use dict-like access** - No need for `.additional_properties`
2. **Use `sync_detailed()`** when you need status codes
3. **Use `sync()`** when you just need the data (returns `None` on error)
4. **Set proper timeouts** in client construction
5. **Use type hints** from helpers module for better IDE support

## Common Pitfalls

❌ **Don't do this:**
```python
data = result.additional_properties["demo1"]["Production"]
```

✅ **Do this instead:**
```python
data = result["demo1"]["Production"]
# or
data = as_dict(result)["demo1"]["Production"]
```
