"""demathpy: PDE/ODE math backend for rde-core."""

from .symbols import normalize_symbols, normalize_lhs
from .pde import (
    PDE,
    normalize_pde,
    init_grid,
    parse_pde,
    step_pdes,
)
from .ode import robust_parse, parse_odes_to_function

__all__ = [
    "PDE",
    "normalize_symbols",
    "normalize_lhs",
    "normalize_pde",
    "init_grid",
    "parse_pde",
    "step_pdes",
    "robust_parse",
    "parse_odes_to_function",
]
