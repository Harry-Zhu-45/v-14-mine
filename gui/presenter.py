"""Presenter layer for Minesweeper solver MVP architecture."""

from core.constants import VARIANT_TYPES
from core.solver import MinesweeperSolver
from core.variant_rules import VariantRules
from gui.game_state import GameState


class MinesweeperPresenter:
    """Mediates between GameState (model) and GUI (view)."""

    def __init__(self, game_state, view):
        """Initialize presenter with game state and view.

        Args:
            game_state: GameState instance
            view: GUI view instance (must have update_display() and show_status() methods)
        """
        self.game_state = game_state
        self.view = view

    def on_cell_click(self, row, col, button):
        """Handle cell click event.

        Args:
            row: Row index of clicked cell
            col: Column index of clicked cell
            button: Mouse button (1 for left, 3 for right)
        """
        if button == 1:  # Left click
            self.game_state.cycle_cell(row, col)
        elif button == 3:  # Right click
            self.game_state.toggle_flag(row, col)

        self.view.update_display()

    def on_solve_click(self):
        """Handle solve button click."""
        try:
            solver = MinesweeperSolver(
                self.game_state.rows,
                self.game_state.cols,
                self.game_state.board_state,
                self.game_state.variant,
                total_mines=self.game_state.total_mines,
            )
            safe, mines = solver.solve()

            if not safe and not mines:
                self.view.show_status("No certain cells found")
                return

            self.game_state.set_solver_results(safe, mines)
            self.view.show_status(f"Safe: {len(safe)} | Mines: {len(mines)}")
            self.view.update_display()

        except ValueError:
            self.view.show_status("No solution for current constraints")
        except Exception as exc:
            self.view.show_status(f"Error: {exc}")

    def on_reset_click(self):
        """Handle reset button click."""
        self.game_state.reset()
        self.view.update_display()

    def on_undo_click(self):
        """Handle undo button click."""
        if self.game_state.undo():
            self.view.update_display()

    def on_variant_change(self):
        """Handle variant change button click."""
        new_variant = self.game_state.change_variant()
        self.view.show_status(f"Variant: {new_variant}")
        self.view.update_display()

    def on_size_change(self, delta):
        """Handle size change button click.

        Args:
            delta: Change in size (positive to increase, negative to decrease)
        """
        if self.game_state.change_size(delta):
            self.view.on_grid_size_changed()
            self.view.update_display()

    def on_mine_count_change(self, delta):
        """Handle mine count change button click.

        Args:
            delta: Change in mine count (positive to increase, negative to decrease)
        """
        if self.game_state.change_mine_count(delta):
            self.view.update_display()

    def get_game_state(self):
        """Get the current game state.

        Returns:
            GameState instance
        """
        return self.game_state

    def get_rows(self):
        """Get number of rows.

        Returns:
            Number of rows
        """
        return self.game_state.rows

    def get_cols(self):
        """Get number of columns.

        Returns:
            Number of columns
        """
        return self.game_state.cols

    def get_variant(self):
        """Get current variant.

        Returns:
            Variant name
        """
        return self.game_state.variant

    def get_total_mines(self):
        """Get total mine count.

        Returns:
            Total mine count
        """
        return self.game_state.total_mines

    def get_board_state(self):
        """Get current board state.

        Returns:
            2D list of cell values
        """
        return self.game_state.board_state

    def get_safe_highlights(self):
        """Get safe cell highlights.

        Returns:
            Set of (row, col) tuples for safe cells
        """
        return self.game_state.safe_highlights

    def get_mine_highlights(self):
        """Get mine cell highlights.

        Returns:
            Set of (row, col) tuples for mine cells
        """
        return self.game_state.mine_highlights

    def is_cell_safe_highlight(self, row, col):
        """Check if cell is highlighted as safe.

        Args:
            row: Row index
            col: Column index

        Returns:
            True if cell is highlighted as safe
        """
        return self.game_state.is_cell_safe_highlight(row, col)

    def is_cell_mine_highlight(self, row, col):
        """Check if cell is highlighted as mine.

        Args:
            row: Row index
            col: Column index

        Returns:
            True if cell is highlighted as mine
        """
        return self.game_state.is_cell_mine_highlight(row, col)
