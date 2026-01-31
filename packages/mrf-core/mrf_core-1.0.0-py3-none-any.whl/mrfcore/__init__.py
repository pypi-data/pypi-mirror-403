"""
MRF-Core
--------

A lightweight, modular, deterministic reasoning engine designed for
LLM autonomy, safety layers, and constraint-based reasoning.

This package exposes the main pipeline class, state object,
diagnostics tools, exceptions, and operator registry.
"""

from .engine import MRFEngine
from .pipeline import Pipeline
from .state import State
from .diagnostics import MRFDiagnostics
from .exceptions import (
    MRFError,
    OperatorNotFound,
    OperatorExecutionError,
    InvalidPipelineConfig,
    DiagnosticsWarning,
)
from .presets import get_preset
from . import operators as operators_module

__all__ = [
    "MRFEngine",
    "Pipeline",
    "State",
    "MRFDiagnostics",
    "MRFError",
    "OperatorNotFound",
    "OperatorExecutionError",
    "InvalidPipelineConfig",
    "DiagnosticsWarning",
    "get_preset",
    "operators_module",
]
