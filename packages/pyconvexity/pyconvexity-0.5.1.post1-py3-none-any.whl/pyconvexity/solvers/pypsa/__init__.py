"""
PyPSA solver integration for PyConvexity.

Provides high-level and low-level APIs for building PyPSA networks from database,
solving them, and storing results back to the database.

After solving, the following prices are stored on each bus:
- marginal_price: LP shadow price of power balance constraint (from PyPSA)
- clearing_price: Pay-as-clear price based on cheapest source with spare capacity
"""

from pyconvexity.solvers.pypsa.api import (
    solve_network,
    build_pypsa_network,
    solve_pypsa_network,
    load_network_components,
    apply_constraints,
    store_solve_results,
)
from pyconvexity.solvers.pypsa.clearing_price import ClearingPriceCalculator

__all__ = [
    "solve_network",
    "build_pypsa_network",
    "solve_pypsa_network",
    "load_network_components",
    "apply_constraints",
    "store_solve_results",
    "ClearingPriceCalculator",
]
