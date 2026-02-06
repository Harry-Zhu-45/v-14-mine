"""Pygame GUI for Minesweeper solver (View layer in MVP)."""

import sys
import time

import pygame

from core.constants import (
    CELL_UNKNOWN,
    CELL_FLAG,
    CELL_UNKNOWN_NUMBER,
    VARIANT_STANDARD,
    VARIANT_KNIGHT,
    VARIANT_MANHATTAN,
    DEFAULT_ROWS,
    DEFAULT_COLS,
    DEFAULT_MINES,
    VARIANT_TYPES,
)
from gui.constants import *
from gui.game_state import GameState
from gui.presenter import MinesweeperPresenter


class MinesweeperPygame:
    """Pygame GUI implementation for the Minesweeper solver (View layer)."""

    def __init__(self):
        pygame.init()

        # UI configuration
        self.ui_font_size = 20
        self.cell_font_size = 22
        self.cell_size = 36
        self.top_bar_height = 80
        self.padding = 10

        # Presenter will be set by main.py
        self.presenter = None

        # Dropdown state
        self.dropdown_open = False
        self.dropdown_items = VARIANT_TYPES
        self.size_dropdown_open = False
        self.size_dropdown_items = ["5", "6", "7", "8"]

        # Input state
        self.mines_input_active = False
        self.mines_input_text = ""

        # Initialize fonts and window
        self._init_fonts()
        self._update_window_size()

        # Status display
        self.clock = pygame.time.Clock()
        self.status_text = ""
        self.status_time = 0.0

    def set_presenter(self, presenter):
        """Set the presenter for this view.

        Args:
            presenter: MinesweeperPresenter instance
        """
        self.presenter = presenter

    def _init_fonts(self):
        preferred = [
            "Noto Sans CJK SC",
            "Noto Sans CJK",
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "Microsoft YaHei",
            "SimHei",
            "PingFang SC",
            "Heiti SC",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        font_path = None
        for name in preferred:
            font_path = pygame.font.match_font(name)
            if font_path:
                break

        self.ui_font = pygame.font.Font(font_path, self.ui_font_size)
        self.cell_font = pygame.font.Font(font_path, self.cell_font_size)

    def _update_window_size(self):
        width, height = self._min_window_size()
        self.window_size = (width, height)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Z3 Minesweeper Solver")

    def _apply_window_size(self, size):
        self.window_size = size
        # self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)

    def _min_window_size(self):
        if not self.presenter:
            width = self.padding * 2 + DEFAULT_COLS * self.cell_size
            height = (
                self.top_bar_height + self.padding * 2 + DEFAULT_ROWS * self.cell_size
            )
            return width, height

        cols = self.presenter.get_cols()
        rows = self.presenter.get_rows()
        width = self.padding * 2 + cols * self.cell_size
        height = self.top_bar_height + self.padding * 2 + rows * self.cell_size
        return width, height

    def _content_offsets(self):
        window_width, window_height = self.screen.get_size()
        min_width, min_height = self._min_window_size()
        offset_x = max(0, (window_width - min_width) // 2)
        offset_y = max(0, (window_height - min_height) // 2)
        return offset_x, offset_y

    def _grid_origin(self):
        offset_x, offset_y = self._content_offsets()
        return (
            offset_x + self.padding,
            offset_y + self.top_bar_height + self.padding,
        )

    def show_status(self, text):
        """Display a status message.

        Args:
            text: Status message text
        """
        self.status_text = text
        self.status_time = time.time()

    def update_display(self):
        """Update the display (called by presenter when state changes)."""
        # This method is called by presenter to trigger redraw
        # The actual drawing happens in run() loop
        pass

    def on_grid_size_changed(self):
        """Called when grid size changes to update window size."""
        width, height = self._min_window_size()
        self._apply_window_size((width, height))

    def _draw_button(self, rect, text, active=True):
        color = (230, 230, 230) if active else (200, 200, 200)
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_GRID_BORDER, rect, width=1, border_radius=4)
        label = self.ui_font.render(text, True, (30, 30, 30))
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

    def _draw_input_box(self, rect, text, active):
        """Draw an input box for entering numbers.

        Args:
            rect: Input box rectangle
            text: Current text in the input box
            active: Whether the input box is active (focused)
        """
        color = (255, 255, 255) if active else (230, 230, 230)
        border_color = (100, 150, 255) if active else COLOR_GRID_BORDER
        border_width = 2 if active else 1

        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(
            self.screen, border_color, rect, width=border_width, border_radius=4
        )

        label = self.ui_font.render(text, True, (30, 30, 30))
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

    def _draw_dropdown(self, rect, current_value, open_state, size_mode=False):
        """Draw a dropdown button and its items if open.

        Args:
            rect: Button rectangle
            current_value: Current selected value
            open_state: Whether dropdown is open
            size_mode: If True, use size dropdown items
        """
        items = self.size_dropdown_items if size_mode else self.dropdown_items

        # Draw dropdown button
        color = (230, 230, 230)
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_GRID_BORDER, rect, width=1, border_radius=4)

        # Draw current value text
        label = self.ui_font.render(current_value, True, (30, 30, 30))
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

        # Draw dropdown arrow
        arrow_size = 6
        arrow_x = rect.right - 15
        arrow_y = rect.centery
        if open_state:
            # Up arrow
            points = [
                (arrow_x, arrow_y - arrow_size),
                (arrow_x - arrow_size, arrow_y + arrow_size),
                (arrow_x + arrow_size, arrow_y + arrow_size),
            ]
        else:
            # Down arrow
            points = [
                (arrow_x, arrow_y + arrow_size),
                (arrow_x - arrow_size, arrow_y - arrow_size),
                (arrow_x + arrow_size, arrow_y - arrow_size),
            ]
        pygame.draw.polygon(self.screen, (80, 80, 80), points)

        # Draw dropdown items if open
        if open_state:
            item_height = 28
            dropdown_bg = pygame.Rect(
                rect.left, rect.bottom + 2, rect.width, len(items) * item_height
            )
            pygame.draw.rect(self.screen, (255, 255, 255), dropdown_bg, border_radius=4)
            pygame.draw.rect(
                self.screen, COLOR_GRID_BORDER, dropdown_bg, width=1, border_radius=4
            )

            for i, item in enumerate(items):
                item_rect = pygame.Rect(
                    rect.left,
                    rect.bottom + 2 + i * item_height,
                    rect.width,
                    item_height,
                )
                if item == current_value:
                    pygame.draw.rect(self.screen, (220, 240, 255), item_rect)
                item_label = self.ui_font.render(item, True, (30, 30, 30))
                item_label_rect = item_label.get_rect(center=item_rect.center)
                self.screen.blit(item_label, item_label_rect)

        return dropdown_bg if open_state else None

    def _draw_label(self, text, x, y, color=(30, 30, 30)):
        label = self.ui_font.render(text, True, color)
        self.screen.blit(label, (x, y))
        return label.get_rect(topleft=(x, y))

    def _layout_ui(self):
        width, _ = self.screen.get_size()
        min_width, _ = self._min_window_size()
        x = self.padding
        y = self.padding

        spacing = 8

        rects = {}

        # Get current state from presenter
        if not self.presenter:
            variant = VARIANT_STANDARD
            rows = DEFAULT_ROWS
            total_mines = DEFAULT_MINES
        else:
            variant = self.presenter.get_variant()
            rows = self.presenter.get_rows()
            total_mines = self.presenter.get_total_mines()

        label_rect = self._draw_label("Rule:", x, y)
        x = label_rect.right + spacing
        rule_rect = pygame.Rect(x, y - 2, 140, 28)
        dropdown_bg = self._draw_dropdown(rule_rect, variant, self.dropdown_open)
        rects["rule"] = rule_rect
        if dropdown_bg:
            rects["dropdown_bg"] = dropdown_bg
        x = rule_rect.right + self.padding

        label_rect = self._draw_label("Size:", x, y)
        x = label_rect.right + spacing
        size_rect = pygame.Rect(x, y - 2, 50, 28)
        size_dropdown_bg = self._draw_dropdown(
            size_rect, str(rows), self.size_dropdown_open, size_mode=True
        )
        rects["size"] = size_rect
        if size_dropdown_bg:
            rects["size_dropdown_bg"] = size_dropdown_bg
        x = size_rect.right + self.padding

        label_rect = self._draw_label("Mines:", x, y)
        x = label_rect.right + spacing
        minus_rect = pygame.Rect(x, y - 2, 26, 28)
        self._draw_button(minus_rect, "-")
        rects["mines_minus"] = minus_rect
        x = minus_rect.right + spacing
        mines_rect = pygame.Rect(x, y - 2, 60, 28)
        mines_text = (
            self.mines_input_text if self.mines_input_active else str(total_mines)
        )
        self._draw_input_box(mines_rect, mines_text, self.mines_input_active)
        rects["mines"] = mines_rect
        x = mines_rect.right + spacing
        plus_rect = pygame.Rect(x, y - 2, 26, 28)
        self._draw_button(plus_rect, "+")
        rects["mines_plus"] = plus_rect
        x = plus_rect.right + self.padding

        window_width, _ = self.screen.get_size()

        # Move to second row for Reset and Solve buttons (left aligned)
        y = self.padding + 34
        x = self.padding

        reset_rect = pygame.Rect(x, y - 2, 90, 28)
        x = reset_rect.right + spacing
        solve_rect = pygame.Rect(x, y - 2, 100, 28)

        self._draw_button(reset_rect, "Reset")
        self._draw_button(solve_rect, "Solve")
        rects["reset"] = reset_rect
        rects["solve"] = solve_rect

        status_y = y + 34
        if self.status_text:
            age = time.time() - self.status_time
            color = (30, 30, 30) if age < 6 else (120, 120, 120)
            self._draw_label(self.status_text, x, status_y, color=color)

        return rects

    def _draw_grid(self):
        if not self.presenter:
            return

        origin_x, origin_y = self._grid_origin()
        board_state = self.presenter.get_board_state()
        rows = self.presenter.get_rows()
        cols = self.presenter.get_cols()

        for r in range(rows):
            for c in range(cols):
                x = origin_x + c * self.cell_size
                y = origin_y + r * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

                val = board_state[r][c]
                if self.presenter.is_cell_safe_highlight(r, c) and (
                    val == CELL_UNKNOWN or val == CELL_UNKNOWN_NUMBER
                ):
                    bg = COLOR_SAFE_HIGHLIGHT
                elif self.presenter.is_cell_mine_highlight(r, c) and (
                    val == CELL_UNKNOWN or val == CELL_UNKNOWN_NUMBER
                ):
                    bg = COLOR_MINE_HIGHLIGHT
                elif val >= 0:
                    bg = COLOR_REVEALED
                else:
                    bg = COLOR_UNKNOWN

                pygame.draw.rect(self.screen, bg, rect)
                pygame.draw.rect(self.screen, COLOR_GRID_BORDER, rect, width=1)

                text = ""
                color = (20, 20, 20)
                if val == CELL_FLAG:
                    text = "F"
                    color = (200, 0, 0)
                elif val == CELL_UNKNOWN_NUMBER:
                    text = "?"
                    color = (100, 100, 100)  # Gray color for unknown number
                elif val >= 0:
                    text = str(val)
                    color = NUMBER_COLORS.get(val, (0, 0, 0))

                if text:
                    label = self.cell_font.render(text, True, color)
                    label_rect = label.get_rect(center=rect.center)
                    self.screen.blit(label, label_rect)

    def _handle_grid_click(self, pos, button):
        """Handle click on grid cell.

        Args:
            pos: (x, y) mouse position
            button: Mouse button (1 for left, 3 for right)
        """
        if not self.presenter:
            return

        origin_x, origin_y = self._grid_origin()
        x, y = pos
        if x < origin_x or y < origin_y:
            return

        col = (x - origin_x) // self.cell_size
        row = (y - origin_y) // self.cell_size

        if not (
            0 <= row < self.presenter.get_rows()
            and 0 <= col < self.presenter.get_cols()
        ):
            return

        self.presenter.on_cell_click(row, col, button)

    def run(self):
        """Main event loop."""
        running = True
        while running:
            self.clock.tick(60)
            self.screen.fill(COLOR_BACKGROUND)

            ui_rects = self._layout_ui()
            self._draw_grid()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in (1, 3):
                        pos = event.pos
                        if ui_rects["rule"].collidepoint(pos):
                            self.dropdown_open = not self.dropdown_open
                            self.size_dropdown_open = False
                        elif "dropdown_bg" in ui_rects and ui_rects[
                            "dropdown_bg"
                        ].collidepoint(pos):
                            # Check which item was clicked
                            item_height = 28
                            rule_rect = ui_rects["rule"]
                            item_index = (pos[1] - rule_rect.bottom - 2) // item_height
                            if 0 <= item_index < len(self.dropdown_items):
                                selected_variant = self.dropdown_items[item_index]
                                if self.presenter.get_variant() != selected_variant:
                                    self.presenter.game_state.variant = selected_variant
                                    self.presenter.game_state.reset(preserve_board=True)
                                    self.show_status(f"Variant: {selected_variant}")
                                    self.update_display()
                            self.dropdown_open = False
                        elif ui_rects["size"].collidepoint(pos):
                            self.size_dropdown_open = not self.size_dropdown_open
                            self.dropdown_open = False
                        elif "size_dropdown_bg" in ui_rects and ui_rects[
                            "size_dropdown_bg"
                        ].collidepoint(pos):
                            # Check which size item was clicked
                            item_height = 28
                            size_rect = ui_rects["size"]
                            item_index = (pos[1] - size_rect.bottom - 2) // item_height
                            if 0 <= item_index < len(self.size_dropdown_items):
                                selected_size = int(
                                    self.size_dropdown_items[item_index]
                                )
                                if self.presenter.get_rows() != selected_size:
                                    self.presenter.on_size_change(
                                        selected_size - self.presenter.get_rows()
                                    )
                            self.size_dropdown_open = False
                        elif "size_minus" in ui_rects and ui_rects[
                            "size_minus"
                        ].collidepoint(pos):
                            self.presenter.on_size_change(-1)
                        elif "size_plus" in ui_rects and ui_rects[
                            "size_plus"
                        ].collidepoint(pos):
                            self.presenter.on_size_change(1)
                        elif ui_rects["mines_minus"].collidepoint(pos):
                            self.presenter.on_mine_count_change(-1)
                            self.mines_input_active = False
                        elif ui_rects["mines_plus"].collidepoint(pos):
                            self.presenter.on_mine_count_change(1)
                            self.mines_input_active = False
                        elif ui_rects["mines"].collidepoint(pos):
                            self.mines_input_active = not self.mines_input_active
                            if self.mines_input_active:
                                self.mines_input_text = ""
                                self.dropdown_open = False
                                self.size_dropdown_open = False
                        elif ui_rects["reset"].collidepoint(pos):
                            self.presenter.on_reset_click()
                            self.mines_input_active = False
                        elif ui_rects["solve"].collidepoint(pos):
                            self.presenter.on_solve_click()
                            self.mines_input_active = False
                        else:
                            self.dropdown_open = False
                            self.size_dropdown_open = False
                            self.mines_input_active = False
                            self._handle_grid_click(pos, event.button)
                elif event.type == pygame.KEYDOWN:
                    if self.mines_input_active:
                        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                            if (
                                self.mines_input_text
                                and self.mines_input_text.isdigit()
                            ):
                                new_mines = int(self.mines_input_text)
                                current_mines = self.presenter.get_total_mines()
                                delta = new_mines - current_mines
                                if delta != 0:
                                    self.presenter.on_mine_count_change(delta)
                            self.mines_input_active = False
                            self.mines_input_text = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.mines_input_text = self.mines_input_text[:-1]
                        elif event.unicode.isdigit():
                            if len(self.mines_input_text) < 3:
                                self.mines_input_text += event.unicode
                    elif event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                        self.presenter.on_undo_click()

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
