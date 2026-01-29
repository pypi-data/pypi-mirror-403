# pd-money

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/pd-money.svg)](https://badge.fury.io/py/pd-money)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive pandas extension for financial data cleaning, performance analysis, and valuation.

## Installation

```bash
pip install pd-money
```

## Quick Start

```python
import pandas as pd
import pd_money

df = pd.DataFrame({"Revenue": ["$1,000.00", "(500.00)", "-"]})
df["Revenue"] = df["Revenue"].money.clean()
# [1000.0, -500.0, 0.0]
```

## Features

### Clean & Format
Transform "dirty" strings from Excel/CSVs into numbers and back again.

```python
# Cleaning
df["Amount"].money.clean(percent=True)
df["Amount"].money.clean(locale="eu") # For 1.234,56 format

# Formatting
df["Amount"].money.format(accounting=True) 
# Results in "$1,000.00" or "($500.00)"
```

### Analysis & Risk
Professional-grade metrics for financial series.

```python
# Growth
df["Price"].money.cagr()

# Risk
df["Price"].money.drawdown()
df["Price"].money.volatility()
df["Price"].money.beta(benchmark=df["Market"])

# Returns
df["CashFlows"].money.xirr()
df["CashFlows"].money.npv(rate=0.08)
```

### Allocation
"Penny-perfect" splitting of amounts.

```python
# Split $100 into 3 equal parts (33.34, 33.33, 33.33)
df["Total"].money.allocate([1, 1, 1])
```

### Validation (Lint)
Detect "Financial Data Smells" instantly.

```python
report = df["Amount"].money.lint()
# [PASS] No nulls found.
# [FAIL] 3 rows contain #DIV/0 errors.
# [WARN] Mixed currency symbols detected: $, €
```

### Utilities
```python
# Scaling
df["Revenue"].money.from_unit("m") # 1.5 -> 1,500,000
df["Revenue"].money.to_unit("m")   # 1,500,000 -> "1.5M"

# FX Conversion
df["Amount"].money.convert(to="USD", rates=rate_dict, dates=df["Date"])

# Reporting
df["Amount"].money.fiscal_year(start_month=10) # FY2024 Q1
df["Amount"].money.profile() # Full summary stats
```

## Why pd-money?

Financial data is notoriously messy. Parentheses for negatives, mixed symbols, and rounding errors make standard pandas operations repetitive and fragile. `pd-money` provides a clean, vectorized accessor (`.money`) to handle these edge cases idiomatically.

## Contributing

We welcome contributions! 
1. Fork the repository.
2. Install in editable mode: `pip install -e .`
3. Add your feature and a test.
4. Submit a Pull Request.

## License

MIT License. See [LICENSE](LICENSE) for details.