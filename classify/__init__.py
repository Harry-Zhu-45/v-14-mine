"""Classify module for board detection and cell recognition."""

# Lazy imports to avoid X11 issues when not using classify features
__all__ = [
    "BoardDetector",
    "CellClassifier",
]


def __getattr__(name):
    """Lazy import of classify module components."""
    if name == "BoardDetector":
        from classify.board_detector import BoardDetector

        return BoardDetector
    elif name == "CellClassifier":
        from classify.classifier import CellClassifier

        return CellClassifier
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
