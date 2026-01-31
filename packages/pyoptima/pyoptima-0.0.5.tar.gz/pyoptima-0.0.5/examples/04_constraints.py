"""
Portfolio constraints: weight bounds, sector caps, exclusion/inclusion.

Use WeightBounds and SumToOne for basic constraints. Use SectorCaps when
you have sector labels. Use ExclusionList/InclusionList to force assets
to zero or restrict to a whitelist.
"""

from pyoptima import (
    PortfolioOptimizer,
    WeightBounds,
    SumToOne,
    SectorCaps,
    ExclusionList,
    InclusionList,
)

expected_returns = [0.10, 0.12, 0.08, 0.09]
covariance_matrix = [
    [0.04, 0.01, 0.02, 0.01],
    [0.01, 0.05, 0.015, 0.01],
    [0.02, 0.015, 0.025, 0.02],
    [0.01, 0.01, 0.02, 0.03],
]
symbols = ["AAPL", "GOOGL", "MSFT", "JPM"]
asset_sectors = {"AAPL": "Tech", "GOOGL": "Tech", "MSFT": "Tech", "JPM": "Finance"}

# Basic: long-only, max 50% per asset, weights sum to 1
opt = PortfolioOptimizer(
    objective="min_volatility",
    constraints=[
        WeightBounds(0, 0.5),
        SumToOne(),
    ],
)
result = opt.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("Weights (no sector caps):", result.weights)

# With sector caps: Tech <= 70%, Finance <= 40%
opt_caps = PortfolioOptimizer(
    objective="min_volatility",
    constraints=[
        WeightBounds(0, 0.5),
        SumToOne(),
        SectorCaps({"Tech": 0.70, "Finance": 0.40}),
    ],
)
result_caps = opt_caps.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
    asset_sectors=asset_sectors,
)
print("Weights (sector caps):", result_caps.weights)

# Exclusion: force some assets to zero
opt_excl = PortfolioOptimizer(
    objective="min_volatility",
    constraints=[
        WeightBounds(0, 0.5),
        SumToOne(),
        ExclusionList(["GOOGL"]),
    ],
)
result_excl = opt_excl.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("Weights (exclude GOOGL):", result_excl.weights)

# Inclusion: only these assets may have non-zero weight
opt_incl = PortfolioOptimizer(
    objective="min_volatility",
    constraints=[
        WeightBounds(0, 0.6),
        SumToOne(),
        InclusionList(["AAPL", "MSFT"]),
    ],
)
result_incl = opt_incl.solve(
    expected_returns=expected_returns,
    covariance_matrix=covariance_matrix,
    symbols=symbols,
)
print("Weights (only AAPL, MSFT):", result_incl.weights)
