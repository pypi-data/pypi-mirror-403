# PyOptima

> **Portfolio optimization with a sklearn-style API and config-driven workflows**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**PyOptima** is a Python package for portfolio optimization. Use a composable, sklearn-style API in code or run from YAML/JSON configs. Many objectives (min volatility, max Sharpe, efficient frontier, risk parity, CVaR, etc.), constraints (sector caps, cardinality, turnover), and solvers (IPOPT, HiGHS, others via Pyomo).

## Features

- **sklearn-style API** – `PortfolioOptimizer(objective=..., constraints=[...]).solve(**data)` with `get_params` / `set_params` / `clone`
- **Config-driven** – `PortfolioOptimizer.from_config(path).solve()` or `run_from_config(path)` for any template
- **Objectives** – min_volatility, max_sharpe, efficient_return, efficient_risk, max_utility, risk_parity, min_cvar, Black-Litterman, and more
- **Constraints** – Weight bounds, sector caps/mins, cardinality, turnover, per-asset bounds
- **Solvers** – IPOPT (default for portfolio), HiGHS, CBC, GLPK, Gurobi via Pyomo
- **IO** – `read_portfolio_csv`, `read_portfolio_json`, pandas-friendly result (`weights_to_dataframe()`)
- **ETL** – Batch optimization and ETL output formatting for pipelines

## Installation

### Core Library

```bash
pip install pyoptima
```

### With Optional Dependencies

```bash
# API server
pip install pyoptima[api]

# UI (Next.js frontend)
pip install pyoptima[ui]

# All optional dependencies
pip install pyoptima[api,ui]
```

### Solvers

PyOptima uses Pyomo, which supports multiple solvers:
- **IPOPT** (default) - Quadratic/nonlinear optimization (required for portfolio optimization)
- **HiGHS** - Linear and mixed-integer programming (included via pip)
- **CBC** - Linear/integer programming
- **GLPK** - Linear programming
- **Gurobi** - Commercial solver (requires license)

**Installation:**
- HiGHS: Automatically installed with PyOptima (`pip install pyoptima`)
- IPOPT: Requires IPOPT C++ libraries first, then `pip install pyoptima` (includes `cyipopt`)
  - Install IPOPT libraries: `conda install -c conda-forge ipopt` (recommended)
  - Or use system packages: `sudo apt-get install coinor-libipopt-dev` (Ubuntu/Debian)
  - PyOptima automatically uses the `ipopt_v2` interface via `cyipopt` for better performance
- See [Solver Installation Guide](docs/SOLVER_INSTALLATION.md) for details

## Quick Start

### Config-driven (recommended)

Config schema: `template`, `data`, `solver`. For portfolio, `data` includes `objective`, `expected_returns`, `covariance_matrix`.

**1. Create a config file** (`portfolio.json`):

```json
{
  "template": "portfolio",
  "data": {
    "objective": "min_volatility",
    "expected_returns": [0.12, 0.11, 0.15],
    "covariance_matrix": [
      [0.04, 0.01, 0.02],
      [0.01, 0.05, 0.01],
      [0.02, 0.01, 0.06]
    ],
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "weight_bounds": [0, 1]
  },
  "solver": { "name": "ipopt" }
}
```

**2. Run from Python**

```python
from pyoptima import run_from_config, PortfolioOptimizer, load_config_file

# One-shot (any template: portfolio, knapsack, lp, ...)
result = run_from_config("portfolio.json")
print(result["weights"], result["portfolio_return"], result["portfolio_volatility"])

# Or: build optimizer from config, then solve (portfolio only)
opt = PortfolioOptimizer.from_config("portfolio.json")
result = opt.solve()  # uses config data
```

**3. CLI**

```bash
pyoptima optimize portfolio.json
```

### Code-only (sklearn-style)

```python
from pyoptima import PortfolioOptimizer

opt = PortfolioOptimizer(objective="min_volatility", max_weight=0.4)
result = opt.solve(
    expected_returns=[0.12, 0.11, 0.15],
    covariance_matrix=[[0.04, 0.01, 0.02], [0.01, 0.05, 0.01], [0.02, 0.01, 0.06]],
    symbols=["AAPL", "MSFT", "GOOGL"],
)
print(result.weights, result.portfolio_return, result.portfolio_volatility)
```

## ETL Integration

PyOptima provides first-class integration with pycharter ETL pipelines. Use `pyoptima.etl.optimize_batch` directly as a pycharter `custom_function`:

### pycharter Configuration (No Bridge Code Needed)

```yaml
# transform.yaml
custom_function:
  module: pyoptima.etl
  function: optimize_batch
  mode: batch
  kwargs:
    objective: min_volatility
    solver: ipopt
```

### Python Usage

```python
from pyoptima.etl import optimize_batch

# ETL input format
data = [{
    "job_id": "growth-2025-01-06",
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "covariance_matrix": {
        "matrix": [[0.04, 0.01, 0.02], [0.01, 0.05, 0.01], [0.02, 0.01, 0.06]],
        "symbols": ["AAPL", "MSFT", "GOOGL"]
    },
    "expected_returns": {"AAPL": 0.12, "MSFT": 0.11, "GOOGL": 0.15},
}]

# Optimize - returns ETL-ready output
results = optimize_batch(data, objective="min_volatility", solver="ipopt")

# Output format ready for loading
print(results[0]["job_id"])        # "growth-2025-01-06"
print(results[0]["weights"])       # {"AAPL": 0.25, "MSFT": 0.40, "GOOGL": 0.35}
print(results[0]["status"])        # "optimal"
print(results[0]["volatility"])    # 0.142
```

**Key features:** pycharter `custom_function` support, input normalization (dict/list/numpy/pandas), ETL-ready output (job_id, weights, status, metrics), all portfolio objectives, per-record error handling.

See [ETL Integration Guide](docs/ETL_INTEGRATION.md) for complete details.

## Constraints

PyOptima supports advanced portfolio constraints beyond basic weight bounds:

### Available Constraints

- **Sector Caps** - Limit total exposure to specific sectors
- **Sector Minimums** - Enforce minimum exposure to sectors
- **Cardinality** - Maximum number of non-zero positions
- **Turnover Limits** - Control trading from current portfolio state
- **Per-Asset Bounds** - Individual min/max bounds per asset
- **Minimum Position Size** - Conditional holding requirements

### Example

```python
from pyoptima import PortfolioOptimizer, SectorCaps, SumToOne, WeightBounds

opt = PortfolioOptimizer(
    objective="min_volatility",
    constraints=[
        WeightBounds(0.05, 0.40),
        SumToOne(),
        SectorCaps({"Technology": 0.50}, asset_sectors={"AAPL": "Technology", "MSFT": "Technology"}),
    ],
)
result = opt.solve(expected_returns=..., covariance_matrix=..., symbols=...)
```

Or pass constraints as kwargs in config `data`:

```python
# In config data
constraints = dict(
    # Sector constraints
    sector_caps={"Technology": 0.40, "Financials": 0.30},
    asset_sectors={
        "AAPL": "Technology",
        "MSFT": "Technology",
        "JPM": "Financials"
    },
    
    # Position limits
    max_positions=15,
    min_position_size=0.02,
    
    # Turnover control
    max_turnover=0.30,
    current_weights={"AAPL": 0.20, "MSFT": 0.30, ...},
    
    # Per-asset bounds
    per_asset_bounds={
        "AAPL": (0.05, 0.30),  # Min 5%, Max 30%
        "MSFT": (0.10, 0.40)
    }
)
```

See [Constraints Documentation](docs/CONSTRAINTS.md) for detailed examples and best practices.

## Available Methods

PyOptima provides 21 portfolio optimization methods organized by category:

### Efficient Frontier Methods
- `min_volatility` - Minimize portfolio volatility
- `max_sharpe` - Maximize Sharpe ratio
- `max_quadratic_utility` - Maximize quadratic utility
- `efficient_risk` - Maximize return for target volatility
- `efficient_return` - Minimize volatility for target return

### Black-Litterman Methods
- `black_litterman_max_sharpe` - BL with max Sharpe objective
- `black_litterman_min_volatility` - BL with min volatility objective
- `black_litterman_quadratic_utility` - BL with quadratic utility objective

### Conditional Value at Risk (CVaR)
- `min_cvar` - Minimize CVaR
- `efficient_cvar_risk` - Maximize return for target CVaR
- `efficient_cvar_return` - Minimize CVaR for target return

### Conditional Drawdown at Risk (CDaR)
- `min_cdar` - Minimize CDaR
- `efficient_cdar_risk` - Maximize return for target CDaR
- `efficient_cdar_return` - Minimize CDaR for target return

### Semivariance Methods
- `min_semivariance` - Minimize downside variance
- `efficient_semivariance_risk` - Maximize return for target semivariance
- `efficient_semivariance_return` - Minimize semivariance for target return

### Hierarchical Risk Parity (HRP)
- `hierarchical_min_volatility` - HRP with min volatility
- `hierarchical_max_sharpe` - HRP with max Sharpe

### Critical Line Algorithm (CLA)
- `cla_min_volatility` - CLA for min volatility
- `cla_max_sharpe` - CLA for max Sharpe

See `examples/` directory for complete, runnable examples of each method.

## Data Format Support

PyOptima automatically detects and converts various data formats:

### Covariance Matrix Formats
- **Nested dict** (ETL format): `{"matrix": [[...], [...]], "symbols": [...]}`
- **Flat dict**: `{"AAPL": {"AAPL": 0.04, "MSFT": 0.01}, ...}`
- **NumPy array**: `np.array([[0.04, 0.01], [0.01, 0.05]])`
- **Pandas DataFrame**: `pd.DataFrame(..., index=symbols, columns=symbols)`

### Expected Returns Formats
- **Flat dict**: `{"AAPL": 0.12, "MSFT": 0.11}`
- **Pandas Series**: `pd.Series([0.12, 0.11], index=["AAPL", "MSFT"])`
- **NumPy array**: `np.array([0.12, 0.11])`

Symbols are automatically aligned between covariance matrix and expected returns.

## Documentation

- [ETL Integration Guide](docs/ETL_INTEGRATION.md) - Using PyOptima with ETL pipeline
- [Constraints Documentation](docs/CONSTRAINTS.md) - Advanced constraint types and examples
- [Usage Guide](USAGE.md) - Detailed usage examples

## API Reference

### Config-driven API

```python
from pyoptima import run_from_config, load_config_file, OptimizationConfig

# One-shot from path or dict
result = run_from_config("portfolio.json")
config = load_config_file("portfolio.json")

# Config shape: template, data, solver (see Quick Start)
```

### PortfolioOptimizer (sklearn-style + from_config)

```python
from pyoptima import PortfolioOptimizer

# Build from config (portfolio only); solve uses config data
opt = PortfolioOptimizer.from_config("min_volatility.json")
result = opt.solve()

# Or solve with different data
result2 = opt.solve(expected_returns=er2, covariance_matrix=cov2, symbols=symbols)
```

### Result Format

Results are returned as dictionaries:

```python
{
    "weights": {"AAPL": 0.30, "MSFT": 0.40, ...},
    "portfolio_return": 0.12,
    "portfolio_volatility": 0.15,
    "sharpe_ratio": 0.80,
    "status": "optimal",
    "objective_value": 0.04,
    "message": "Optimization successful"
}
```

### ETL Integration

```python
from pyoptima.etl import optimize_batch

# ETL (pycharter custom_function)
results = optimize_batch(
    data=[{"expected_returns": {...}, "covariance_matrix": {...}}],
    objective="min_volatility",
    max_weight=0.40,
    solver="ipopt"
)
```

### Constraints via kwargs

```python
# Pass constraints as kwargs to optimize_batch
results = optimize_batch(
    data,
    objective="min_volatility",
    sector_caps={"Technology": 0.40},
    asset_sectors={"AAPL": "Technology", ...},
    max_assets=10,
    max_turnover=0.30,
    current_weights={"AAPL": 0.20, ...},
    max_weight=0.30,
)
```

## CLI Usage

### Optimization

```bash
# Optimize from config file
pyoptima optimize config.json

# With output file
pyoptima optimize config.json --output results.json --pretty
```

### API Server

```bash
# Start API server
pyoptima api --host 0.0.0.0 --port 8000

# With auto-reload (development)
pyoptima api --host 0.0.0.0 --port 8000 --reload
```

### UI

```bash
# Development mode
pyoptima ui dev

# Build for production
pyoptima ui build

# Serve built UI
pyoptima ui serve
```

## Development Setup

```bash
# Clone repository
cd pyoptima

# Install in development mode
pip install -e ".[api,ui]"

# Run tests
pytest tests/

# Run API server
pyoptima api --host 0.0.0.0 --port 8000

# Run UI (development)
pyoptima ui dev
```

## Requirements

- Python 3.10+
- Pyomo (for optimization)
- NumPy, Pandas (for data handling)
- Pydantic >= 2.0.0 (for configuration)
- Optional: FastAPI, Uvicorn (for API server)
- Optional: Next.js, React (for UI)

## Project Structure

```
pyoptima/
├── pyoptima/           # Core package
│   ├── methods/        # Optimization methods (registry)
│   ├── constraints/    # Constraint system
│   ├── adapters/       # Data format adapters
│   ├── integration/   # ETL integration
│   ├── utils/          # Utilities (data formats, Pyomo helpers)
│   └── models/         # Configuration models
├── api/                # FastAPI server (optional)
├── ui/                 # Next.js UI (optional)
├── examples/           # Example configurations and scripts
├── tests/              # Test suite
└── docs/               # Documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Made with ❤️ for the Python optimization community**

