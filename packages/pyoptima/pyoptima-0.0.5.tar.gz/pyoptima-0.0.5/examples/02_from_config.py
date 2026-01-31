"""
Portfolio optimization from a config file.

Load a YAML/JSON config with template=portfolio and data (objective,
expected_returns, covariance_matrix, symbols, etc.). Build the optimizer
with from_config() and call solve() with no arguments to use config data.
"""

from pathlib import Path

from pyoptima import PortfolioOptimizer

# Path relative to this script; adjust if running from repo root
examples_dir = Path(__file__).resolve().parent
config_path = examples_dir / "configs" / "portfolio_min_vol.yaml"

opt = PortfolioOptimizer.from_config(config_path)
result = opt.solve()

print(f"Status: {result.status.value}")
if result.portfolio_volatility is not None:
    print(f"Volatility: {result.portfolio_volatility:.2%}")
if result.portfolio_return is not None:
    print(f"Return: {result.portfolio_return:.2%}")
print("Weights:", result.weights)
if result.solver_message:
    print("Solver message:", result.solver_message)
