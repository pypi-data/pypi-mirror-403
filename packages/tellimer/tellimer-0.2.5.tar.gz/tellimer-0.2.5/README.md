# Tellimer Python SDK

A Python client library for accessing Tellimer's data through their REST API. This SDK provides convenient access to macroeconomic data, parallel FX data, probability of default data, and other financial datasets.

## Installation

```bash
pip install tellimer
```

## Quick Start

```python
import tellimer

# Initialize the client with your API key
api_key = "your_api_key_here"
client = tellimer.Client(api_key=api_key)

# Get macroeconomic data
result = client.data.macro_data.get(
    countries=["ARG"],
    indicators=["PCPIPCH"],  # Inflation rate
    start_date="2020-01-01",
    end_date="2023-12-31"
)

print(result.data)
```

## Authentication

The SDK requires an API key for authentication. You can obtain an API key from your Tellimer account dashboard.

```python
client = tellimer.Client(
    api_key="your_api_key_here",
    timeout=30  # Optional: request timeout in seconds
)
```

## Core Components

### Client

The main client class that provides access to all API endpoints.

#### Parameters
- `api_key` (str): Your Tellimer API key
- `timeout` (float, optional): Request timeout in seconds (default: 30)

### Result

A data class that contains the response from data requests.

#### Attributes
- `data` (pandas.DataFrame): The requested data in DataFrame format with multi-level columns
- `metadata` (list[dict]): Metadata about the indicators and countries

## Data Access

### Available Datasets

The SDK currently supports the following datasets:

- `macro_data`: Macroeconomic indicators (searchable)
- `parallel_fx`: Parallel foreign exchange data
- `probability_default`: Probability of default data with optional contribution breakdowns

```python
# List all available datasets
datasets = client.data.list_datasets()
print(datasets)  # ['macro_data', 'parallel_fx']
```

### Macroeconomic Data (`macro_data`)

The macro data client provides access to searchable macroeconomic indicators.

#### Search Indicators

Search for available indicators using natural language queries:

```python
# Basic search
indicators = client.data.macro_data.search(
    query="inflation",
    limit=5
)

# Search with filters
from tellimer import Filter

source_filter = Filter(field="source_name").equals("IMFWEO")
country_filter = Filter(field="country_iso").equals("ARG")

indicators = client.data.macro_data.search(
    query="inflation",
    limit=10,
    filters=[source_filter, country_filter]
)
```

#### Get Data

Retrieve actual data for specific indicators and countries:

```python
# Get data for specific indicators and countries
result = client.data.macro_data.get(
    countries=["ARG", "BRA", "MEX"],
    indicators=["PCPIPCH", "NGDP_RPCH"],  # Inflation and GDP growth
    start_date="2020-01-01",
    end_date="2023-12-31"
)

# Access the data
df = result.data  # pandas DataFrame with multi-level columns
metadata = result.metadata  # List of indicator metadata
```

### Parallel FX Data (`parallel_fx`)

Access parallel foreign exchange rate data:

```python
# Get available countries for parallel FX data
countries = client.data.parallel_fx.available_countries()

# Get parallel FX data
result = client.data.parallel_fx.get(
    countries=["ARG", "PAK"],
    start_date="2025-07-01",
    end_date="2025-09-01"
)

print(result.data.head())
```

### Probability of Default Data (`probability_default`)

Access probability of default data with optional contribution breakdowns:

```python
# Get available countries for probability of default data
countries = client.data.probability_default.available_countries()

# Get probability of default data for specific countries
result = client.data.probability_default.get(
    countries=["ARG", "BRA"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)

print(result.data.head())
# DataFrame with date index and country columns
```

#### Including Contribution Breakdowns

You can request additional contribution data that breaks down the probability of default into component factors:

```python
# Get probability of default with contribution breakdowns
result = client.data.probability_default.get(
    countries=["ARG"],
    include_contributions=True,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# DataFrame has multi-level columns: (metric, country)
# Metrics include probabilityOfDefault plus contribution factors
df = result.data
print(df.columns)  # MultiIndex with (metric, country) pairs
```

#### Fetching All Countries

If no countries are specified, data for all available countries is returned:

```python
# Get probability of default data for all available countries
result = client.data.probability_default.get()
print(result.data.head())
```

## Filtering

The `Filter` class allows you to create complex filters for searching indicators:

### Available Filter Operations

```python
from tellimer import Filter

# Equality
filter1 = Filter("source_name").equals("IMFWEO")
filter2 = Filter("country_iso").not_equals("NGA")
```

### Date Filtering

`get` functions allows *optional* `start_date` and `end_date` arguments, which can be iso format strings, `date` or `datetime` objects. Either or both can also be left blank:

```python
from datetime import date, datetime

# String formats
start_date = "2025-05-01" # YYYY-MM-DD
start_date = "2025/05/01" # YYYY/MM/DD

# Python date objects
start_date = date(2025, 5, 1)               
start_date = datetime(2025, 5, 1, 12, 0, 0) 

# Set to `None` or can just be left blank
end_date = None

result = client.data.parallel_fx.get(
    countries=["ARG", "PAK"],
    start_date=start_date,
    end_date=end_date,
)
```

## Working with Results

### Data Structure

The returned data is structured as a pandas DataFrame with multi-level columns:

```python
result = client.data.macro_data.get(
    countries=["ARG", "NGA"],
    indicators=["PCPIPCH", "NGDP_RPCH"]
)

# The DataFrame has a multi-level column structure
# Level 0: Indicator codes
# Level 1: Country codes
# Index: Dates

df = result.data
print(df.columns)  # MultiIndex with (indicator, country) pairs
print(df.index)    # DatetimeIndex

# Access specific series
argentina_inflation = df[("PCPIPCH", "ARG")]
nigeria_gdp_growth = df[("NGDP_RPCH", "NGA")]
```

### Metadata

Each result includes metadata about the indicators:

```python
result = client.data.macro_data.get(countries=["ARG"], indicators=["PCPIPCH"])

for meta in result.metadata:
    print(f"Indicator: {meta['indicator']}")
    print(f"Country: {meta['country']}")
    print(f"Name: {meta.get('name', 'N/A')}")
    print(f"Source: {meta.get('source_name', 'N/A')}")
    print("---")
```

## Advanced Usage

### Error Handling

The SDK provides specific error classes for different types of API errors. These errors are automatically raised based on HTTP status codes:

```python
# Import specific error classes from the errors module
from tellimer.errors import (
    AuthError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    MethodNotAllowedError,
    RateLimitError,
    InternalServerError,
    BadGatewayError,
    ServiceUnavailableError,
    GatewayTimeoutError
)

try:
    result = client.data.macro_data.get(
        countries=["INVALID"],
        indicators=["INVALID_INDICATOR"]
    )
except AuthError:
    print("Invalid API key")
except BadRequestError:
    print("Invalid request parameters")
except NotFoundError:
    print("Resource not found")
except RateLimitError:
    print("Rate limit exceeded - please wait before making more requests")
except InternalServerError:
    print("Server error - please try again later")
except Exception as e:
    print(f"Unexpected error: {e}")
```

#### Error Types

The SDK maps HTTP status codes to specific error classes:

- `400 Bad Request` → `BadRequestError`: Invalid request parameters
- `401 Unauthorized` → `AuthError`: Invalid or missing API key  
- `403 Forbidden` → `ForbiddenError`: Access denied
- `404 Not Found` → `NotFoundError`: Resource not found
- `405 Method Not Allowed` → `MethodNotAllowedError`: HTTP method not allowed
- `429 Too Many Requests` → `RateLimitError`: Rate limit exceeded
- `500 Internal Server Error` → `InternalServerError`: Server error
- `502 Bad Gateway` → `BadGatewayError`: Bad gateway
- `503 Service Unavailable` → `ServiceUnavailableError`: Service unavailable
- `504 Gateway Timeout` → `GatewayTimeoutError`: Gateway timeout

#### Handling Specific Errors

```python
import tellimer
from tellimer.errors import AuthError, RateLimitError, NotFoundError

client = tellimer.Client(api_key="your_api_key")

try:
    result = client.data.macro_data.get(
        countries=["ARG"],
        indicators=["PCPIPCH"]
    )
except AuthError:
    print("Please check your API key")
except RateLimitError:
    print("Rate limit exceeded. Please wait before making more requests.")
except NotFoundError:
    print("The requested data was not found")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

### Custom Timeouts

Configure request timeouts for your specific needs:

```python
# Short timeout for quick operations
client = tellimer.Client(api_key="your_key", timeout=10)

# Longer timeout for large data requests
client = tellimer.Client(api_key="your_key", timeout=60)
```

### Data Export

Since results are pandas DataFrames, you can easily export to various formats:

```python
result = client.data.macro_data.get(countries=["ARG"], indicators=["PCPIPCH"])

# Export to CSV
result.data.to_csv("argentina_inflation.csv")

# Export to Excel
result.data.to_excel("argentina_inflation.xlsx")

# Export to JSON
result.data.to_json("argentina_inflation.json")
```

## Examples

### Example 1: Inflation Analysis

```python
import tellimer
import matplotlib.pyplot as plt

client = tellimer.Client(api_key="your_api_key")

# Get inflation data for Latin American countries
result = client.data.macro_data.get(
    countries=["ARG", "BRA", "MEX", "COL", "CHL"],
    indicators=["PCPIPCH"],  # Inflation, average consumer prices
    start_date="2020-01-01",
    end_date="2023-12-31"
)

# Plot the data
df = result.data
df.plot(kind='line', figsize=(12, 6))
plt.title('Inflation Rates - Latin America')
plt.ylabel('Inflation Rate (%)')
plt.show()
```

### Example 2: GDP Growth Comparison

```python
# Search for GDP growth indicators
indicators = client.data.macro_data.search(
    query="GDP growth real",
    limit=5
)

# Get the data
result = client.data.macro_data.get(
    countries=["ARG", "BRA", "MEX", "COL", "CHL"],
    indicators=["NGDP_RPCH"],  # Real GDP growth
    start_date="2015-01-01"
)

# Calculate average growth rates
df = result.data
avg_growth = df.mean()
print("Average GDP Growth Rates:")
print(avg_growth)
```

### Example 3: Filtered Search

```python
# Create filters for World Bank data on emerging markets
source_filter = Filter("source_name").equals("World Bank")

# Search for unemployment data
indicators = client.data.macro_data.search(
    query="unemployment rate",
    limit=10,
    filters=[source_filter]
)

print(f"Found {len(indicators)} unemployment indicators from World Bank")
```

### Example 4: Probability of Default Analysis

```python
import tellimer
import matplotlib.pyplot as plt

client = tellimer.Client(api_key="your_api_key")

# Get available countries for probability of default data
countries = client.data.probability_default.available_countries()
print(f"Available countries: {countries}")

# Get probability of default data for emerging market countries
result = client.data.probability_default.get(
    countries=["ARG", "BRA", "TUR", "ZAF"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Plot probability of default over time
df = result.data
df.plot(kind='line', figsize=(12, 6))
plt.title('Probability of Default - Emerging Markets')
plt.ylabel('Probability of Default')
plt.xlabel('Date')
plt.legend(title='Country')
plt.show()
```

### Example 5: Probability of Default with Contribution Breakdown

```python
import tellimer

client = tellimer.Client(api_key="your_api_key")

# Get probability of default with contribution breakdown
result = client.data.probability_default.get(
    countries=["ARG"],
    include_contributions=True,
    start_date="2024-01-01",
    end_date="2024-06-30"
)

# The DataFrame has multi-level columns when contributions are included
df = result.data
print("Available metrics:")
print(df.columns.tolist())

# Access specific metrics
# The structure is (metric, country) when contributions are included
# Metrics may include: probabilityOfDefault, creditRisk, marketRisk, etc.
```

### Example 6: Comparing Probability of Default Across Regions

```python
import tellimer
import pandas as pd

client = tellimer.Client(api_key="your_api_key")

# Get data for all available countries
result = client.data.probability_default.get(
    start_date="2024-06-01",
    end_date="2024-06-30"
)

df = result.data

# Calculate average probability of default for each country
avg_pod = df.mean().sort_values(ascending=False)
print("Average Probability of Default by Country:")
print(avg_pod)

# Identify highest risk countries
high_risk = avg_pod[avg_pod > avg_pod.median()]
print(f"\nCountries with above-median risk: {high_risk.index.tolist()}")
```

## API Reference

### Client Class

```python
class Client:
    def __init__(self, api_key: str, timeout: float = 30)
```

### DataClient Class

```python
class DataClient:
    def list_datasets() -> list[str]

    # Dataset-specific clients
    macro_data: _BaseSearchableDataset
    parallel_fx: _BaseDataset
    probability_default: ProbabilityDefaultClient
```

### Dataset Methods

```python
# For searchable datasets (macro_data)
class _BaseSearchableDataset:
    def search(query: str, limit: int = 5, filters: list[Filter] = None) -> list[dict]
    def get(countries: list[str] | str, indicators: list[str] | str = None, 
            start_date: str = None, end_date: str = None) -> Result

# For non-searchable datasets (parallel_fx)
class _BaseDataset:
    def available_countries() -> list[str]
    def get(countries: list[str] | str, start_date: str = None,
            end_date: str = None) -> Result

# For probability of default data
class ProbabilityDefaultClient:
    def available_countries() -> list[str]
    def get(countries: list[str] | str | None = None,
            include_contributions: bool = False,
            start_date: str = None, end_date: str = None) -> Result
```

### Filter Class

```python
class Filter:
    def __init__(field: str)
    def equals(value: str) -> Filter
    def not_equals(value: str) -> Filter
    def greater_than(value: str) -> Filter
    def greater_than_or_equal_to(value: str) -> Filter
    def less_than(value: str) -> Filter
    def less_than_or_equal_to(value: str) -> Filter
```

## Requirements

- Python >= 3.10
- httpx >= 0.24.1
- pandas >= 2.0.0

## Support

For support, please contact the Tellimer team or refer to the API documentation.

## Version

Current version: 0.2.5