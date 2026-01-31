# waterworksai

[![PyPI version](https://img.shields.io/pypi/v/waterworksai)](https://pypi.org/project/waterworksai/)
[![Python Version](https://img.shields.io/pypi/pyversions/waterworksai)](https://pypi.org/project/waterworksai/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Official Python client for the [waterworks.ai](https://waterworks.ai) API, providing seamless access to:

- Inflow & Infiltration decomposition
- Water component analysis
- 48-hour flow forecasting
- Leakage & sewer blockage detection
- Pipe survival & remaining useful life (RUL) estimation

---

## Installation

```bash
pip install waterworksai
```

## Quick Start

```python
import pandas as pd
from waterworksai import WaterworksClient
from waterworksai.adapters import from_dataframe
from waterworksai.tasks.forecast import Forecast48h

# Load your hourly flow CSV
df = pd.read_csv("hourly_flow.csv")
df["Date"] = pd.to_datetime(df["Date"])

# Convert to canonical TimeSeriesPoint
points = from_dataframe(df, time_col="Date", value_col="Volume")

# Initialize API client
client = WaterworksClient(api_key="YOUR_API_KEY")

# Run 48-hour forecast
result = client.post(
    "forecast",
    Forecast48h(df=points).payload()
)

print("Forecast MAE:", result["MAE"])
print("Forecast points:", result["forecast"])

```

## Examples
Examples

Full working examples for all tasks are available in the examples/ folder:

- forecast_48h.py

- inflow_infiltration.py

- leakage.py

- pipe_survival.py

These scripts demonstrate DataFrame integration, API calls, and result handling.

## License
MIT © waterworks.ai