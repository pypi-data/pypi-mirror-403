"""
Operator Modules for MRF-Core
-----------------------------

Each operator is a composable, atomic transformation used by the MRF
reasoning pipeline. Operators MUST subclass BaseOperator and implement:

    - name (str)
    - run(state, **kwargs)

This package exposes all built-in operators and the registry utilities.
"""

from .base import BaseOperator
from .transform import Transform
from .summarize import Summarize
from .evaluate import Evaluate
from .filter import Filter
from .inspect import Inspect
from .rewrite import Rewrite

# Optional: add new operators here automatically
BUILTIN_OPERATORS = {
    "transform": Transform,
    "summarize": Summarize,
    "evaluate": Evaluate,
    "filter": Filter,
    "inspect": Inspect,
    "rewrite": Rewrite,
}

__all__ = [
    "BaseOperator",
    "Transform",
    "Summarize",
    "Evaluate",
    "Filter",
    "Inspect",
    "Rewrite",
    "BUILTIN_OPERATORS",
]
