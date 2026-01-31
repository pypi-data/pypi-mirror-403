"""
Portfolio optimization quickstart.

Minimal example: create a PortfolioOptimizer, pass expected returns and
covariance matrix, then solve and read weights and metrics.
"""

from pyoptima import PortfolioOptimizer, WeightBounds, SumToOne

# Inputs: expected returns (annualized), covariance matrix, optional symbols
expected_returns = [0.10, 0.12, 0.08]
covariance_matrix = [
    [0.04, 0.01, 0.02],
    [0.01, 0.05, 0.015],
    [0.02, 0.015, 0.025],
]
symbols = ["AAPL", "GOOGL", "MSFT"]

# Build optimizer: objective + constraints
opt = PortfolioOptimizer(
    objective="min_volatility",
    constraints=[WeightBounds(0, 0.5), SumToOne()],
)

# Solve
result = opt.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)

# Results
print(f"Status: {result.status.value}")
print(f"Volatility: {result.portfolio_volatility:.2%}")
print(f"Return: {result.portfolio_return:.2%}")
print("Weights:", result.weights)

# Optional: export to DataFrame (requires pandas)
# df = result.weights_to_dataframe()
# print(df)
