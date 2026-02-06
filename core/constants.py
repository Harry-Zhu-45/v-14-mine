"""Constants for the Minesweeper solver."""

# Cell state constants
CELL_UNKNOWN = -1
CELL_FLAG = -2
CELL_UNKNOWN_NUMBER = -3  # Cell is a number (0-8) but exact value unknown

# Variant type constants
VARIANT_STANDARD = "Standard"
VARIANT_KNIGHT = "Knight"
VARIANT_MANHATTAN = "Manhattan"
VARIANT_ODD_EVEN = "OddEven"

# Default configuration
DEFAULT_ROWS = 10
DEFAULT_COLS = 10
DEFAULT_MINES = 10

# All variant types
VARIANT_TYPES = [VARIANT_STANDARD, VARIANT_KNIGHT, VARIANT_MANHATTAN, VARIANT_ODD_EVEN]
