"""Main entry point for the Minesweeper solver application."""

import sys

from PyQt6.QtWidgets import QApplication

from gui.pyqt_gui import MinesweeperPyQt
from gui.presenter import MinesweeperPresenter
from models.game_state import GameState

if __name__ == "__main__":
    # Create Qt application
    app = QApplication(sys.argv)

    # Create MVP components
    game_state = GameState(rows=5, cols=5, variant="Standard", total_mines=10)
    view = MinesweeperPyQt()
    presenter = MinesweeperPresenter(game_state, view)

    # Connect view to presenter
    view.set_presenter(presenter)

    # Run the application
    view.run()

    sys.exit(app.exec())
