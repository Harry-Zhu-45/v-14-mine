"""Game state model for Minesweeper solver."""

from core.constants import CELL_UNKNOWN, CELL_FLAG, CELL_UNKNOWN_NUMBER


class GameState:
    """Manages the game state including board, history, and configuration."""

    def __init__(self, rows=10, cols=10, variant="Standard", total_mines=10):
        """Initialize game state with given configuration.

        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            variant: Game variant ("Standard", "Knight", or "Manhattan")
            total_mines: Total number of mines in the grid
        """
        self.rows = rows
        self.cols = cols
        self.variant = variant
        self.total_mines = total_mines

        # Initialize board state
        self.board_state = [[CELL_UNKNOWN] * cols for _ in range(rows)]
        self.history = []  # For undo functionality
        self.safe_highlights = set()  # Cells highlighted as safe by solver
        self.mine_highlights = set()  # Cells highlighted as mines by solver

    def reset(self, preserve_board: bool = False):
        """Reset the game state to initial configuration.

        Args:
            preserve_board: If True, preserve the board state (for variant switching)
        """
        if not preserve_board:
            self.board_state = [[CELL_UNKNOWN] * self.cols for _ in range(self.rows)]
        self.history = []
        self.safe_highlights = set()
        self.mine_highlights = set()

    def cycle_cell(self, row, col):
        """Cycle a cell through possible values (unknown → 0 → 1 → 2 → ... → 8 → unknown).

        Args:
            row: Row index of the cell
            col: Column index of the cell
        """
        current = self.board_state[row][col]
        self._push_history(row, col, current)

        if current == CELL_UNKNOWN:
            new_val = CELL_UNKNOWN_NUMBER
        elif current == CELL_FLAG:
            new_val = CELL_UNKNOWN_NUMBER
        elif current == CELL_UNKNOWN_NUMBER:
            new_val = 0
        elif current == 8:
            new_val = CELL_UNKNOWN_NUMBER
        else:
            new_val = current + 1

        self.board_state[row][col] = new_val
        self._clear_highlights()

    def toggle_flag(self, row, col):
        """Toggle a cell between unknown and flag states.

        Args:
            row: Row index of the cell
            col: Column index of the cell
        """
        current = self.board_state[row][col]
        self._push_history(row, col, current)

        if current == CELL_FLAG:
            self.board_state[row][col] = CELL_UNKNOWN
        else:
            self.board_state[row][col] = CELL_FLAG

        self._clear_highlights()

    def undo(self):
        """Undo the last cell modification."""
        if not self.history:
            return False

        r, c, previous_val = self.history.pop()
        self.board_state[r][c] = previous_val
        self._clear_highlights()
        return True

    def _push_history(self, row, col, value):
        """Record a move in history for undo functionality.

        Args:
            row: Row index of the cell
            col: Column index of the cell
            value: Previous value of the cell
        """
        self.history.append((row, col, value))

    def _clear_highlights(self):
        """Clear solver highlights."""
        self.safe_highlights = set()
        self.mine_highlights = set()

    def change_size(self, delta):
        """Change grid size by delta, maintaining square grid.

        Args:
            delta: Change in size (positive to increase, negative to decrease)

        Returns:
            True if size changed, False otherwise
        """
        new_size = max(3, min(20, self.rows + delta))
        if new_size == self.rows:
            return False

        self.rows = new_size
        self.cols = new_size
        self.total_mines = min(self.total_mines, self.rows * self.cols)
        self.reset()
        return True

    def change_mine_count(self, delta):
        """Change total mine count by delta.

        Args:
            delta: Change in mine count (positive to increase, negative to decrease)

        Returns:
            True if mine count changed, False otherwise
        """
        max_mines = self.rows * self.cols
        new_mines = max(0, min(max_mines, self.total_mines + delta))
        if new_mines == self.total_mines:
            return False

        self.total_mines = new_mines
        return True

    def change_variant(self):
        """Cycle to next game variant.

        Returns:
            The new variant name
        """
        from core.constants import VARIANT_TYPES

        idx = VARIANT_TYPES.index(self.variant) if self.variant in VARIANT_TYPES else 0
        self.variant = VARIANT_TYPES[(idx + 1) % len(VARIANT_TYPES)]
        return self.variant

    def get_cell_value(self, row, col):
        """Get the value of a cell.

        Args:
            row: Row index
            col: Column index

        Returns:
            Cell value (CELL_UNKNOWN, CELL_FLAG, or 0-8)
        """
        return self.board_state[row][col]

    def set_cell_value(self, row, col, value):
        """Set the value of a cell.

        Args:
            row: Row index
            col: Column index
            value: New cell value
        """
        self.board_state[row][col] = value

    def is_cell_safe_highlight(self, row, col):
        """Check if a cell is highlighted as safe by solver.

        Args:
            row: Row index
            col: Column index

        Returns:
            True if cell is highlighted as safe
        """
        return (row, col) in self.safe_highlights

    def is_cell_mine_highlight(self, row, col):
        """Check if a cell is highlighted as mine by solver.

        Args:
            row: Row index
            col: Column index

        Returns:
            True if cell is highlighted as mine
        """
        return (row, col) in self.mine_highlights

    def set_solver_results(self, safe_cells, mine_cells):
        """Set solver results as highlights.

        Args:
            safe_cells: List of (row, col) tuples for safe cells
            mine_cells: List of (row, col) tuples for mine cells
        """
        self.safe_highlights = set(safe_cells)
        self.mine_highlights = set(mine_cells)
