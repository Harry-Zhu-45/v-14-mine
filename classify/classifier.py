"""Cell classifier based on template matching with OCR fallback."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from core.constants import CELL_FLAG, CELL_UNKNOWN, CELL_UNKNOWN_NUMBER


class CellClassifier:
    """Classifies minesweeper cell states from single-cell images."""

    TEMPLATE_SIZE = 72
    INNER_MARGIN_RATIO = 0.1

    def __init__(
        self,
        pattern_dir: Optional[str] = None,
        state_threshold: float = 0.72,
        digit_threshold: float = 0.74,
        weak_threshold: float = 0.64,
    ):
        """Initialize classifier and preload templates.

        Args:
            pattern_dir: Optional template directory path.
            state_threshold: Confidence threshold for blank/flag/question templates.
            digit_threshold: Confidence threshold for digit templates.
            weak_threshold: Fallback threshold when OCR fails.
        """
        self.pattern_dir = Path(pattern_dir) if pattern_dir else Path(__file__).resolve().parent / "pattern"
        self.state_threshold = state_threshold
        self.digit_threshold = digit_threshold
        self.weak_threshold = weak_threshold

        self.state_label_map = {
            "flag": CELL_FLAG,
            "question": CELL_UNKNOWN_NUMBER,
        }
        self.digit_label_map = {str(i): i for i in range(9)}
        self.blank_label = "blank"
        self.blank_std_threshold = 16.0
        self.min_symbol_std = 8.0

        self.templates: Dict[str, np.ndarray] = {}
        self._load_templates()

    def classify(self, cell_image: np.ndarray, debug: bool = False) -> int:
        """Classify a single cell image."""
        if cell_image is None or cell_image.size == 0:
            return CELL_UNKNOWN

        h, w = cell_image.shape[:2]
        if h < 5 or w < 5:
            return CELL_UNKNOWN

        if not self.templates:
            if debug:
                print("  [WARN] No templates loaded, using OCR only")
            ocr_result = self._recognize_by_ocr(cell_image, debug=debug)
            return ocr_result if ocr_result >= 0 else CELL_UNKNOWN

        normalized = self._normalize_cell(cell_image)
        texture_std = float(np.std(normalized))

        best_state_label, best_state_score = self._best_match(normalized, list(self.state_label_map.keys()))
        best_digit_label, best_digit_score = self._best_match(normalized, list(self.digit_label_map.keys()))
        blank_score = self._single_match(normalized, self.blank_label)

        if debug:
            print(f"  [STATE] label={best_state_label}, score={best_state_score:.3f}")
            print(f"  [DIGIT] label={best_digit_label}, score={best_digit_score:.3f}")
            print(f"  [BLANK] score={blank_score:.3f}, texture_std={texture_std:.2f}")

        if self._is_state_confident(best_state_label, best_state_score, texture_std):
            if debug:
                print(f"  [MATCH] state={best_state_label}, score={best_state_score:.3f}")
            return self.state_label_map[best_state_label]

        if texture_std <= self.blank_std_threshold and blank_score >= self.weak_threshold:
            if debug:
                print(f"  [MATCH] blank score={blank_score:.3f}, texture_std={texture_std:.2f}")
            return CELL_UNKNOWN

        if best_digit_label and best_digit_score >= self.digit_threshold:
            if debug:
                print(f"  [MATCH] digit={best_digit_label}, score={best_digit_score:.3f}")
            return self.digit_label_map[best_digit_label]

        ocr_result = self._recognize_by_ocr(cell_image, debug=debug)
        if 0 <= ocr_result <= 8:
            if debug:
                print(f"  [OCR] result={ocr_result}")
            return ocr_result

        fallback_label, fallback_score, fallback_state = self._pick_fallback(
            best_state_label,
            best_state_score,
            best_digit_label,
            best_digit_score,
        )
        if fallback_label and fallback_score >= self.weak_threshold:
            if debug:
                print(f"  [WEAK] label={fallback_label}, score={fallback_score:.3f}")
            return fallback_state

        if blank_score >= self.weak_threshold and texture_std <= self.blank_std_threshold:
            if debug:
                print(f"  [WEAK] blank score={blank_score:.3f}, texture_std={texture_std:.2f}")
            return CELL_UNKNOWN

        if debug:
            print("  [UNKNOWN] no confident match")
        return CELL_UNKNOWN

    def classify_board(self, cell_images: List[List[np.ndarray]], debug: bool = False) -> List[List[int]]:
        """Classify all cells in a board."""
        board_state = []
        for r, row in enumerate(cell_images):
            row_state = []
            for c, cell in enumerate(row):
                if debug:
                    print(f"  Cell ({r},{c}):", end="")
                row_state.append(self.classify(cell, debug=debug))
            board_state.append(row_state)
        return board_state

    def _load_templates(self) -> None:
        """Load and preprocess templates from pattern directory."""
        labels = [self.blank_label] + list(self.state_label_map.keys()) + [str(i) for i in range(10)]
        for label in labels:
            template_path = self.pattern_dir / f"{label}.png"
            if not template_path.exists():
                continue

            template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
            if template is None or template.size == 0:
                continue

            self.templates[label] = self._normalize_cell(template)

    def _normalize_cell(self, image: np.ndarray) -> np.ndarray:
        """Normalize cell image to an inner grayscale patch for matching."""
        bgr = self._ensure_bgr(image)
        resized = cv2.resize(bgr, (self.TEMPLATE_SIZE, self.TEMPLATE_SIZE), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        inner = self._crop_inner(gray)
        equalized = cv2.equalizeHist(inner)
        return cv2.GaussianBlur(equalized, (3, 3), 0)

    def _ensure_bgr(self, image: np.ndarray) -> np.ndarray:
        """Convert supported image formats to BGR."""
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return image

    def _crop_inner(self, gray: np.ndarray) -> np.ndarray:
        """Crop inner region to reduce border/grid-line interference."""
        h, w = gray.shape
        margin = max(1, int(min(h, w) * self.INNER_MARGIN_RATIO))
        if h - 2 * margin < 8 or w - 2 * margin < 8:
            return gray
        return gray[margin:h - margin, margin:w - margin]

    def _best_match(self, query: np.ndarray, labels: List[str]) -> Tuple[Optional[str], float]:
        """Return best template label and confidence score among candidate labels."""
        best_label = None
        best_score = -1.0

        for label in labels:
            score = self._single_match(query, label)
            if score > best_score:
                best_score = score
                best_label = label

        return best_label, best_score

    def _single_match(self, query: np.ndarray, label: str) -> float:
        """Return confidence score [0, 1] for a single template label."""
        template = self.templates.get(label)
        if template is None:
            return -1.0

        query_f = query.astype(np.float32)
        template_f = template.astype(np.float32)

        query_std = float(np.std(query_f))
        template_std = float(np.std(template_f))

        if query_std < 1e-6 or template_std < 1e-6:
            mae = float(np.mean(np.abs(query_f - template_f))) / 255.0
            return max(0.0, 1.0 - mae)

        score = float(cv2.matchTemplate(query_f, template_f, cv2.TM_CCOEFF_NORMED)[0][0])
        if np.isnan(score):
            return -1.0
        return score

    def _pick_fallback(
        self,
        state_label: Optional[str],
        state_score: float,
        digit_label: Optional[str],
        digit_score: float,
    ) -> Tuple[Optional[str], float, int]:
        """Pick strongest candidate across state and digit templates."""
        if state_score >= digit_score and state_label:
            return state_label, state_score, self.state_label_map[state_label]
        if digit_label:
            return digit_label, digit_score, self.digit_label_map[digit_label]
        return None, -1.0, CELL_UNKNOWN

    def _is_state_confident(self, label: Optional[str], score: float, texture_std: float) -> bool:
        """Validate state-template match confidence with texture constraints."""
        if not label or score < self.state_threshold:
            return False
        if label in {"flag", "question"} and texture_std < self.min_symbol_std:
            return False
        return True

    def _recognize_by_ocr(self, cell_image: np.ndarray, debug: bool = False) -> int:
        """Use OCR as fallback when template confidence is insufficient."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            if debug:
                print("  [OCR] pytesseract or PIL unavailable")
            return -1

        gray = cv2.cvtColor(self._ensure_bgr(cell_image), cv2.COLOR_BGR2GRAY)
        gray = self._crop_inner(gray)
        enlarged = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        binaries = [
            self._to_binary_otsu(enlarged),
            cv2.adaptiveThreshold(
                enlarged,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                17,
                2,
            ),
            cv2.adaptiveThreshold(
                enlarged,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                17,
                2,
            ),
        ]

        config = "--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789"
        for idx, binary in enumerate(binaries):
            bordered = cv2.copyMakeBorder(binary, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=255)
            text = pytesseract.image_to_string(Image.fromarray(bordered), config=config).strip()
            parsed = self._extract_digit(text)
            if 0 <= parsed <= 8:
                if debug:
                    print(f"  [OCR] strategy={idx}, raw={text!r}, parsed={parsed}")
                return parsed

        return -1

    def _to_binary_otsu(self, gray: np.ndarray) -> np.ndarray:
        """Convert grayscale to Otsu binary with dark text on light background."""
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if np.sum(binary == 0) > np.sum(binary == 255):
            return cv2.bitwise_not(binary)
        return binary

    def _extract_digit(self, text: str) -> int:
        """Extract first valid digit 0-8 from OCR output."""
        normalized = (
            text.replace("O", "0")
            .replace("o", "0")
            .replace("S", "5")
            .replace("s", "5")
            .replace("I", "1")
            .replace("l", "1")
            .replace("|", "1")
        )
        digits = [ch for ch in normalized if ch.isdigit()]
        if not digits:
            return -1

        value = int(digits[0])
        if 0 <= value <= 8:
            return value
        return -1
