"""Minesweeper solver using Z3 theorem prover."""

from typing import List, Tuple, Optional

import z3

from .constants import CELL_UNKNOWN, CELL_FLAG, CELL_UNKNOWN_NUMBER, VARIANT_ODD_EVEN
from .variant_rules import VariantRules


class MinesweeperSolver:
    """Solver for Minesweeper puzzles using Z3 constraint solving."""

    def __init__(
        self,
        rows: int,
        cols: int,
        board_state: List[List[int]],
        variant_type: str,
        total_mines: Optional[int] = None,
    ):
        """Initialize the solver.

        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            board_state: 2D list of cell values (-2=flag, -1=unknown, 0-8=revealed count)
            variant_type: Type of variant ("Standard", "Knight", "Manhattan", or "OddEven")
            total_mines: Optional total number of mines in the grid
        """
        self.rows = rows
        self.cols = cols
        self.board_state = board_state
        self.variant = variant_type
        self.total_mines = total_mines

        # Cache for neighbor calculations
        self.neighbor_cache = None
        self.is_odd_matrix = None

        # Precompute data for performance optimization
        self._precompute_data()

    def _precompute_data(self):
        """Precompute neighbor and parity information for performance optimization."""
        # Precompute neighbor cache for all cells
        self._precompute_neighbors()

        # Precompute parity matrix for OddEven variant
        if self.variant == VARIANT_ODD_EVEN:
            self._precompute_parity()

    def _precompute_neighbors(self):
        """Precompute neighbor lists for all cells to avoid repeated calculations."""
        self.neighbor_cache = {}
        for r in range(self.rows):
            for c in range(self.cols):
                self.neighbor_cache[(r, c)] = VariantRules.get_neighbors(
                    r, c, self.rows, self.cols, self.variant
                )

    def _precompute_parity(self):
        """Precompute odd/even parity matrix for OddEven variant."""
        self.is_odd_matrix = [
            [VariantRules.is_odd_cell(r, c) for c in range(self.cols)]
            for r in range(self.rows)
        ]

    def solve(self) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Solve the current board state.

        Returns:
            Tuple of (safe_cells, mine_cells) where each is a list of (row, col) tuples

        Raises:
            ValueError: If no solution exists for the current constraints
        """
        # Create Z3 variables for each cell (0=empty, 1=mine)
        z3_vars = [
            [z3.Int(f"c_{r}_{c}") for c in range(self.cols)] for r in range(self.rows)
        ]
        solver = z3.Solver()

        # Constraint: each cell is either 0 (empty) or 1 (mine)
        for r in range(self.rows):
            for c in range(self.cols):
                solver.add(z3.And(z3_vars[r][c] >= 0, z3_vars[r][c] <= 1))

        unknown_cells = []

        # Add constraints based on current board state
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.board_state[r][c]

                if val >= 0:  # Revealed cell with number
                    solver.add(z3_vars[r][c] == 0)  # Revealed cells cannot be mines
                    nbs = self.neighbor_cache[(r, c)]

                    if self.variant == VARIANT_ODD_EVEN:
                        # OddEven variant: number = |odd_neighbors_mines - even_neighbors_mines|
                        weighted_terms = []
                        for nr, nc in nbs:
                            # 这里的正负权重定义依然保留，但因为后面用了绝对值，方向反了也没关系
                            weight = 1 if self.is_odd_matrix[nr][nc] else -1
                            weighted_terms.append(z3_vars[nr][nc] * weight)

                        # 计算加权和 (即：奇数雷数 - 偶数雷数)
                        weighted_sum = z3.Sum(weighted_terms)

                        # === 修改开始 ===
                        # 绝对值约束：weighted_sum 等于 val 或者 -val
                        # 这行代码替换了原来的: solver.add(z3.Sum(weighted_terms) == val)
                        solver.add(z3.Or(weighted_sum == val, weighted_sum == -val))
                        # === 修改结束 ===
                elif val == CELL_UNKNOWN_NUMBER:
                    # Cell is a number (0-8) but exact value unknown
                    solver.add(z3_vars[r][c] == 0)  # Not a mine
                    nbs = self.neighbor_cache[(r, c)]

                    if self.variant == VARIANT_ODD_EVEN:
                        # OddEven variant: number = |odd_neighbors_mines - even_neighbors_mines|
                        # Use weighted sum: odd neighbors weight = 1, even neighbors weight = -1
                        weighted_terms = []
                        for nr, nc in nbs:
                            weight = 1 if self.is_odd_matrix[nr][nc] else -1
                            weighted_terms.append(z3_vars[nr][nc] * weight)

                        # Constraint: weighted_sum is between -8 and 8
                        weighted_sum = z3.Sum(weighted_terms)
                        solver.add(weighted_sum >= -8)
                        solver.add(weighted_sum <= 8)
                    else:
                        # Standard variants: number of neighboring mines is between 0 and 8
                        neighbor_mines = z3.Sum([z3_vars[nr][nc] for nr, nc in nbs])
                        solver.add(neighbor_mines >= 0)
                        solver.add(neighbor_mines <= 8)
                elif val == CELL_UNKNOWN:
                    unknown_cells.append((r, c))
                elif val == CELL_FLAG:
                    solver.add(z3_vars[r][c] == 1)  # Flagged cells are mines

        # Optional: total mines constraint
        if self.total_mines is not None:
            solver.add(
                z3.Sum(
                    [z3_vars[r][c] for r in range(self.rows) for c in range(self.cols)]
                )
                == self.total_mines
            )

        if not unknown_cells:
            return [], []

        # Check if solution exists
        if solver.check() == z3.unsat:
            raise ValueError("No solution for current constraints")

        # Find safe cells and mine cells
        safe_cells = []
        mine_cells = []

        for r, c in unknown_cells:
            # Test if cell must be a mine (cannot be empty)
            solver.push()
            solver.add(z3_vars[r][c] == 0)
            if solver.check() == z3.unsat:
                mine_cells.append((r, c))
            solver.pop()

            # Test if cell must be empty (cannot be a mine)
            solver.push()
            solver.add(z3_vars[r][c] == 1)
            if solver.check() == z3.unsat:
                safe_cells.append((r, c))
            solver.pop()

        return safe_cells, mine_cells
