"""
Common portfolio objectives.

Same data, different objectives: min volatility, max Sharpe, target return
(efficient frontier), and max utility (risk-aversion).
"""

from pyoptima import PortfolioOptimizer, WeightBounds, SumToOne

expected_returns = [0.10, 0.12, 0.08]
covariance_matrix = [
    [0.04, 0.01, 0.02],
    [0.01, 0.05, 0.015],
    [0.02, 0.015, 0.025],
]
symbols = ["AAPL", "GOOGL", "MSFT"]
constraints = [WeightBounds(0, 0.6), SumToOne()]

# 1. Minimum volatility
opt_minvol = PortfolioOptimizer(objective="min_volatility", constraints=constraints)
r_minvol = opt_minvol.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("min_volatility:", r_minvol.portfolio_volatility, r_minvol.portfolio_return)

# 2. Maximum Sharpe ratio
opt_sharpe = PortfolioOptimizer(
    objective="max_sharpe",
    risk_free_rate=0.02,
    constraints=constraints,
)
r_sharpe = opt_sharpe.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("max_sharpe:", r_sharpe.sharpe_ratio, r_sharpe.portfolio_return)

# 3. Target return (efficient frontier: minimize risk for given return)
opt_eff = PortfolioOptimizer(
    objective="efficient_return",
    target_return=0.10,
    constraints=constraints,
)
r_eff = opt_eff.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("efficient_return(10%):", r_eff.portfolio_volatility, r_eff.portfolio_return)

# 4. Max utility (risk aversion)
opt_util = PortfolioOptimizer(
    objective="max_utility",
    risk_aversion=2.0,
    constraints=constraints,
)
r_util = opt_util.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("max_utility(λ=2):", r_util.portfolio_volatility, r_util.portfolio_return)
