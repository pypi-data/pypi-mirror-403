# PyOptima portfolio examples

Concise examples for portfolio optimization with the `pyoptima` package.

## Examples

| File | Description |
|------|-------------|
| **01_quickstart.py** | Minimal flow: `PortfolioOptimizer` + `solve(expected_returns, covariance_matrix, symbols)` and read `result.weights`, `result.portfolio_volatility`, etc. |
| **02_from_config.py** | Load a YAML/JSON config with `PortfolioOptimizer.from_config(path)` and call `solve()` with no arguments to use config data. |
| **03_objectives.py** | Same data, different objectives: `min_volatility`, `max_sharpe`, `efficient_return` (target return), `max_utility` (risk aversion). |
| **04_constraints.py** | Weight bounds, `SumToOne`, `SectorCaps`, `ExclusionList`, and `InclusionList`. |

## Configs

- **configs/portfolio_min_vol.yaml** – Minimum volatility with weight bounds.
- **configs/portfolio_max_sharpe.yaml** – Maximum Sharpe with risk-free rate.

Config format: `template: portfolio`, `data` with `objective`, `expected_returns`, `covariance_matrix`, `symbols`, and optional `min_weight`/`max_weight`, `risk_free_rate`; `solver` with `name` (e.g. `ipopt`).

## Run

From the repo root (with `pyoptima` installed or on `PYTHONPATH`):

```bash
python examples/01_quickstart.py
python examples/02_from_config.py
python examples/03_objectives.py
python examples/04_constraints.py
```

Or from the `examples` directory:

```bash
cd examples
python 01_quickstart.py
```

## API summary

- **Code-only:** `PortfolioOptimizer(objective=..., constraints=[...]).solve(expected_returns=..., covariance_matrix=..., symbols=...)` → `OptimizationResult` (`.weights`, `.portfolio_return`, `.portfolio_volatility`, `.sharpe_ratio`, `.weights_to_dataframe()`).
- **Config-driven:** `PortfolioOptimizer.from_config(path_or_dict).solve()` uses data from the config; override by passing kwargs to `solve(**data)`.
