# Sematryx Python SDK

Official Python SDK for [Sematryx](https://sematryx.com) - AI-powered optimization that explains itself.

## Installation

```bash
pip install sematryx
```

## Quick Start

```python
from sematryx import Sematryx

client = Sematryx(api_key="sk-your-api-key")

# Simple optimization
result = client.optimize(
    objective="minimize",
    variables=[
        {"name": "x", "bounds": (-5, 5)},
        {"name": "y", "bounds": (-5, 5)},
    ],
    objective_function="x**2 + y**2",
)

print(f"Solution: {result.solution}")  # {'x': 0.0, 'y': 0.0}
print(f"Explanation: {result.explanation}")
```

## Features

- **Simple API** - One function call to optimize
- **Explainable Results** - Understand why the optimizer made its decisions
- **Audit Trails** - Full traceability for regulated industries
- **Private Learning** - Your optimizations improve over time
- **Domain Libraries** - Pre-built for finance, healthcare, supply chain

## CLI Usage

```bash
# Install
pip install sematryx

# Set API key
export sematryx_API_KEY=sk-your-api-key

# Run optimization
sematryx optimize "x**2 + y**2" --bounds '{"x": [-5, 5], "y": [-5, 5]}'

# Check usage
sematryx usage
```

## Async Support

```python
from sematryx import AsyncSematryx

async with AsyncSematryx(api_key="sk-...") as client:
    result = await client.optimize(
        objective="minimize",
        variables=[{"name": "x", "bounds": (-5, 5)}],
        objective_function="x**2",
    )
```

## Portfolio Optimization

```python
result = client.optimize_portfolio(
    assets=["AAPL", "GOOGL", "MSFT", "AMZN"],
    returns=[0.12, 0.10, 0.08, 0.15],
    covariance=[...],  # 4x4 covariance matrix
    target_return=0.10,
    max_position=0.4,
    explanation_level=3,
)

print(result.solution)  # {'AAPL': 0.25, 'GOOGL': 0.20, ...}
print(result.explanation)  # "Allocated to maximize Sharpe ratio..."
```

## Private Learning Store

Your optimizations improve over time:

```python
result = client.optimize(
    ...,
    learning={
        "read_from_private": True,   # Learn from your past optimizations
        "write_to_private": True,    # Store this result for future learning
    }
)
```

## Documentation

Full documentation at [sematryx.com/docs](https://sematryx.com/docs)

## License

MIT

