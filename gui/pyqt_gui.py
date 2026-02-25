"""PyQt6 GUI for Minesweeper solver (View layer in MVP)."""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QSpinBox,
    QLabel,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPen

from core.constants import (
    CELL_UNKNOWN,
    CELL_FLAG,
    CELL_UNKNOWN_NUMBER,
    VARIANT_STANDARD,
    DEFAULT_SIZE,
    DEFAULT_MINES,
    VARIANT_TYPES,
)

from gui.constants import (
    COLOR_SAFE_HIGHLIGHT,
    COLOR_MINE_HIGHLIGHT,
    COLOR_REVEALED,
    COLOR_UNKNOWN,
    COLOR_GRID_BORDER,
    COLOR_BACKGROUND,
    NUMBER_COLORS,
)


class GridWidget(QWidget):
    """Custom widget for drawing the Minesweeper grid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.presenter = None
        self.cell_size = 36
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_presenter(self, presenter):
        """Set the presenter for this grid."""
        self.presenter = presenter

    def _calculate_cell_size(self):
        """Calculate cell size based on widget size."""
        if not self.presenter:
            return self.cell_size

        cols = self.presenter.get_cols()
        rows = self.presenter.get_rows()

        available_width = self.width()
        available_height = self.height()

        cell_width = available_width / cols
        cell_height = available_height / rows

        cell_size = min(cell_width, cell_height)
        return max(20, min(80, int(cell_size)))

    def _grid_origin(self):
        """Calculate grid origin for centering."""
        if not self.presenter:
            return (0, 0)

        cols = self.presenter.get_cols()
        rows = self.presenter.get_rows()
        cell_size = self._calculate_cell_size()

        grid_width = cols * cell_size
        grid_height = rows * cell_size

        grid_x = (self.width() - grid_width) // 2
        grid_y = (self.height() - grid_height) // 2

        return (grid_x, grid_y)

    def paintEvent(self, event):
        """Draw the grid."""
        from PyQt6.QtGui import QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), QColor(*COLOR_BACKGROUND))

        if not self.presenter:
            return

        origin_x, origin_y = self._grid_origin()
        board_state = self.presenter.get_board_state()
        rows = self.presenter.get_rows()
        cols = self.presenter.get_cols()
        cell_size = self._calculate_cell_size()

        # Draw cells
        for r in range(rows):
            for c in range(cols):
                x = origin_x + c * cell_size
                y = origin_y + r * cell_size

                val = board_state[r][c]

                # Determine background color
                if self.presenter.is_cell_safe_highlight(r, c) and (
                    val == CELL_UNKNOWN or val == CELL_UNKNOWN_NUMBER
                ):
                    bg_color = QColor(*COLOR_SAFE_HIGHLIGHT)
                elif self.presenter.is_cell_mine_highlight(r, c) and (
                    val == CELL_UNKNOWN or val == CELL_UNKNOWN_NUMBER
                ):
                    bg_color = QColor(*COLOR_MINE_HIGHLIGHT)
                elif val >= 0:
                    bg_color = QColor(*COLOR_REVEALED)
                else:
                    bg_color = QColor(*COLOR_UNKNOWN)

                # Draw cell background
                painter.fillRect(x, y, cell_size, cell_size, bg_color)

                # Draw cell border
                painter.setPen(QPen(QColor(*COLOR_GRID_BORDER), 1))
                painter.drawRect(x, y, cell_size, cell_size)

                # Draw cell text
                text = ""
                color = QColor(20, 20, 20)
                if val == CELL_FLAG:
                    text = "F"
                    color = QColor(200, 0, 0)
                elif val == CELL_UNKNOWN_NUMBER:
                    text = "?"
                    color = QColor(100, 100, 100)
                elif val >= 0:
                    text = str(val)
                    rgb = NUMBER_COLORS.get(val, (0, 0, 0))
                    color = QColor(*rgb)

                if text:
                    font_size = max(10, int(cell_size * 0.5))
                    font = QFont()
                    font.setPointSize(font_size)
                    font.setBold(True)
                    painter.setFont(font)
                    painter.setPen(color)
                    painter.drawText(
                        x, y, cell_size, cell_size, Qt.AlignmentFlag.AlignCenter, text
                    )

    def mousePressEvent(self, event):
        """Handle mouse click on grid."""
        if not self.presenter:
            return

        origin_x, origin_y = self._grid_origin()
        x = event.position().x()
        y = event.position().y()

        if x < origin_x or y < origin_y:
            return

        cell_size = self._calculate_cell_size()
        col = int((x - origin_x) // cell_size)
        row = int((y - origin_y) // cell_size)

        if not (
            0 <= row < self.presenter.get_rows()
            and 0 <= col < self.presenter.get_cols()
        ):
            return

        button = event.button()
        if button == Qt.MouseButton.LeftButton:
            self.presenter.on_cell_click(row, col, 1)
        elif button == Qt.MouseButton.RightButton:
            self.presenter.on_cell_click(row, col, 3)

        self.update()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if (
            event.key() == Qt.Key.Key_Z
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            if self.presenter:
                self.presenter.on_undo_click()
                self.update()


class MinesweeperPyQt(QMainWindow):
    """PyQt6 GUI implementation for the Minesweeper solver (View layer)."""

    def __init__(self):
        super().__init__()

        # Presenter will be set by main.py
        self.presenter = None

        # Status display
        self.status_text = ""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._clear_status)

        # Initialize UI
        self._init_ui()

    def set_presenter(self, presenter):
        """Set the presenter for this view.

        Args:
            presenter: MinesweeperPresenter instance
        """
        self.presenter = presenter
        self.grid_widget.set_presenter(presenter)

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Z3 Minesweeper Solver")
        self.setMinimumSize(750, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar for controls
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        # Large font for controls (2x default)
        large_font = QFont()
        large_font.setPointSize(18)

        # Rule selector
        rule_label = QLabel("Rule:")
        rule_label.setFont(large_font)
        top_layout.addWidget(rule_label)

        self.rule_combo = QComboBox()
        self.rule_combo.setFont(large_font)
        self.rule_combo.addItems(VARIANT_TYPES)
        self.rule_combo.setCurrentText(VARIANT_STANDARD)
        self.rule_combo.currentTextChanged.connect(self._on_rule_changed)
        self.rule_combo.setFixedWidth(160)
        top_layout.addWidget(self.rule_combo)

        top_layout.addSpacing(10)

        # Size selector
        size_label = QLabel("Size:")
        size_label.setFont(large_font)
        top_layout.addWidget(size_label)

        self.size_combo = QComboBox()
        self.size_combo.setFont(large_font)
        self.size_combo.addItems(["5", "6", "7", "8"])
        self.size_combo.setCurrentText(str(DEFAULT_SIZE))
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        self.size_combo.setFixedWidth(70)
        top_layout.addWidget(self.size_combo)

        top_layout.addSpacing(10)

        # Mines count
        mines_label = QLabel("Mines:")
        mines_label.setFont(large_font)
        top_layout.addWidget(mines_label)

        self.mines_spin = QSpinBox()
        self.mines_spin.setFont(large_font)
        self.mines_spin.setRange(0, 100)
        self.mines_spin.setValue(DEFAULT_MINES)
        self.mines_spin.valueChanged.connect(self._on_mines_changed)
        self.mines_spin.setFixedWidth(90)
        top_layout.addWidget(self.mines_spin)

        top_layout.addStretch()

        # Solve button
        self.solve_btn = QPushButton("Solve")
        self.solve_btn.setFont(large_font)
        self.solve_btn.clicked.connect(self._on_solve_clicked)
        self.solve_btn.setFixedWidth(100)
        top_layout.addWidget(self.solve_btn)

        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFont(large_font)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        self.reset_btn.setFixedWidth(100)
        top_layout.addWidget(self.reset_btn)

        main_layout.addWidget(top_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #1e1e1e;")
        main_layout.addWidget(self.status_label)

        # Grid widget
        self.grid_widget = GridWidget()
        main_layout.addWidget(self.grid_widget, 1)

    def _on_rule_changed(self, rule):
        """Handle rule change."""
        if self.presenter:
            self.presenter.on_variant_set(rule)

    def _on_size_changed(self, size_str):
        """Handle size change."""
        if self.presenter:
            new_size = int(size_str)
            current_size = self.presenter.get_rows()
            delta = new_size - current_size
            if delta != 0:
                self.presenter.on_size_change(delta)

    def _on_mines_changed(self, value):
        """Handle mines count change."""
        if self.presenter:
            current_mines = self.presenter.get_total_mines()
            delta = value - current_mines
            if delta != 0:
                self.presenter.on_mine_count_change(delta)

    def _on_solve_clicked(self):
        """Handle solve button click."""
        if self.presenter:
            self.presenter.on_solve_click()

    def _on_reset_clicked(self):
        """Handle reset button click."""
        if self.presenter:
            self.presenter.on_reset_click()

    def show_status(self, text):
        """Display a status message.

        Args:
            text: Status message text
        """
        self.status_text = text
        self.status_label.setText(text)
        self.status_label.setStyleSheet("color: #1e1e1e;")
        self.status_timer.start(6000)

    def _clear_status(self):
        """Clear status after timeout."""
        self.status_timer.stop()
        if self.status_label.text():
            self.status_label.setStyleSheet("color: #787878;")

    def update_display(self):
        """Update the display (called by presenter when state changes)."""
        self.grid_widget.update()

    def on_grid_size_changed(self):
        """Called when grid size changes to update UI."""
        if self.presenter:
            self.size_combo.blockSignals(True)
            self.size_combo.setCurrentText(str(self.presenter.get_rows()))
            self.size_combo.blockSignals(False)

            self.mines_spin.blockSignals(True)
            self.mines_spin.setMaximum(
                self.presenter.get_rows() * self.presenter.get_cols()
            )
            self.mines_spin.setValue(self.presenter.get_total_mines())
            self.mines_spin.blockSignals(False)

        self.grid_widget.update()

    def run(self):
        """Main entry point to run the application."""
        self.show()
