"""Paramax - Paramaterizations and constraints for PyTrees."""

from importlib.metadata import version

from .wrappers import (
    AbstractUnwrappable,
    NonTrainable,
    Parameterize,
    RealToIncreasingOnInterval,
    WeightNormalization,
    contains_unwrappables,
    non_trainable,
    unwrap,
)

__version__ = version("paramax")

__all__ = [
    "AbstractUnwrappable",
    "NonTrainable",
    "Parameterize",
    "WeightNormalization",
    "RealToIncreasingOnInterval",
    "contains_unwrappables",
    "non_trainable",
    "unwrap",
]
