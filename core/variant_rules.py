"""Variant rules for Minesweeper neighbor calculations."""

from typing import List, Tuple

from .constants import (
    VARIANT_STANDARD,
    VARIANT_KNIGHT,
    VARIANT_MANHATTAN,
    VARIANT_ODD_EVEN,
    VARIANT_CROSS,
)


class VariantRules:
    """Static class for calculating neighbors based on different rule variants."""

    @staticmethod
    def is_odd_cell(r: int, c: int) -> bool:
        """Check if a cell is on an odd position (using checkerboard pattern).

        Args:
            r: Row index
            c: Column index

        Returns:
            True if the cell is odd, False if even
        """
        return (r + c) % 2 == 1

    @staticmethod
    def get_neighbors(
        r: int, c: int, rows: int, cols: int, variant_type: str = VARIANT_STANDARD
    ) -> List[Tuple[int, int]]:
        """Get neighbors of a cell based on the variant type.

        Args:
            r: Row index
            c: Column index
            rows: Total rows in the grid
            cols: Total columns in the grid
            variant_type: Type of variant ("Standard", "Knight", "Manhattan", or "OddEven")

        Returns:
            List of (row, col) tuples for valid neighbors
        """
        standard_offsets = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        knight_offsets = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]

        if variant_type == VARIANT_STANDARD:
            offsets = standard_offsets
        elif variant_type == VARIANT_KNIGHT:
            offsets = knight_offsets
        elif variant_type == VARIANT_MANHATTAN:
            offsets = standard_offsets + [(-2, 0), (2, 0), (0, -2), (0, 2)]
        elif variant_type == VARIANT_ODD_EVEN:
            offsets = standard_offsets
        elif variant_type == VARIANT_CROSS:
            offsets = [
                (-2, 0),
                (-1, 0),
                (1, 0),
                (2, 0),
                (0, -2),
                (0, -1),
                (0, 1),
                (0, 2),
            ]
        else:
            offsets = standard_offsets

        neighbors = []
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbors.append((nr, nc))
        return neighbors
