"""Core module for Minesweeper solver."""

from .variant_rules import VariantRules
from .solver import MinesweeperSolver
from .constants import (
    CELL_UNKNOWN,
    CELL_FLAG,
    CELL_UNKNOWN_NUMBER,
    VARIANT_STANDARD,
    VARIANT_KNIGHT,
    VARIANT_ODD_EVEN,
    VARIANT_CROSS,
    VARIANT_PARTITION,
    VARIANT_TYPES,
    DEFAULT_SIZE,
    DEFAULT_MINES,
)

__all__ = [
    "VariantRules",
    "MinesweeperSolver",
    "CELL_UNKNOWN",
    "CELL_FLAG",
    "CELL_UNKNOWN_NUMBER",
    "VARIANT_STANDARD",
    "VARIANT_KNIGHT",
    "VARIANT_ODD_EVEN",
    "VARIANT_CROSS",
    "VARIANT_PARTITION",
    "VARIANT_TYPES",
    "DEFAULT_SIZE",
    "DEFAULT_MINES",
]
