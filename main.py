"""Main entry point for the Minesweeper solver application."""

from gui.pygame_gui import MinesweeperPygame
from gui.game_state import GameState
from gui.presenter import MinesweeperPresenter

if __name__ == "__main__":
    # Create MVP components
    game_state = GameState(rows=5, cols=5, variant="Standard", total_mines=10)
    view = MinesweeperPygame()
    presenter = MinesweeperPresenter(game_state, view)

    # Connect view to presenter
    view.set_presenter(presenter)

    # Run the application
    view.run()
