"""Cell classifier for recognizing minesweeper cell states."""

from typing import List

import cv2
import numpy as np

from core.constants import (
    CELL_UNKNOWN,
    CELL_FLAG,
    CELL_UNKNOWN_NUMBER,
)


class CellClassifier:
    """Classifies minesweeper cell states from images."""

    # Minesweeper color definitions (BGR format)
    # These are typical colors used in classic minesweeper
    NUMBER_COLORS = {
        0: (192, 192, 192),  # Empty cell (revealed)
        1: (0, 0, 255),  # Blue
        2: (0, 128, 0),  # Green
        3: (0, 0, 255),  # Red
        4: (128, 0, 0),  # Dark blue
        5: (0, 0, 128),  # Maroon
        6: (128, 128, 0),  # Teal
        7: (0, 0, 0),  # Black
        8: (128, 128, 128),  # Gray
    }

    # Cell background colors
    UNCOVERED_COLOR = (192, 192, 192)  # Light gray (revealed)
    COVERED_COLOR = (192, 192, 192)  # Covered cell color varies

    def __init__(self):
        """Initialize the classifier."""

    def classify(self, cell_image: np.ndarray, debug: bool = False) -> int:
        """Classify a single cell image.

        Args:
            cell_image: BGR image of a single cell
            debug: If True, print debug information

        Returns:
            Cell state constant (CELL_UNKNOWN, CELL_FLAG, 0-8, etc.)
        """
        if cell_image is None or cell_image.size == 0:
            return CELL_UNKNOWN

        # Resize to standard size for consistent analysis
        h, w = cell_image.shape[:2]
        if h < 5 or w < 5:
            return CELL_UNKNOWN

        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        std_dev = np.std(gray)

        # Check for flag first (flags can be on covered or revealed cells)
        is_flag = self._is_flag(cell_image)
        if is_flag:
            if debug:
                print(f"  [FLAG] brightness={avg_brightness:.1f}, std={std_dev:.1f}")
            return CELL_FLAG

        # Determine if cell is revealed (opened) or covered
        # Key insight: covered cells have black center, revealed cells have non-black content
        is_revealed = self._is_revealed_cell(cell_image, gray)

        if not is_revealed:
            if debug:
                print(f"  [COVERED] brightness={avg_brightness:.1f}, std={std_dev:.1f}")
            return CELL_UNKNOWN

        # Revealed cell - try to recognize number
        if debug:
            print(f"  [REVEALED] brightness={avg_brightness:.1f}, std={std_dev:.1f}")

        # Check for question mark
        if self._is_question_mark(cell_image):
            if debug:
                print(f"  [QUESTION] brightness={avg_brightness:.1f}, std={std_dev:.1f}")
            return CELL_UNKNOWN_NUMBER

        # Check for mine (for exploded cells)
        if self._is_mine(cell_image):
            if debug:
                print(f"  [MINE] brightness={avg_brightness:.1f}, std={std_dev:.1f}")
            return CELL_FLAG  # Treat as flag/mine

        # Try to recognize number
        number = self._recognize_number(cell_image, debug=debug)
        if debug:
            print(f"  [NUMBER {number}] brightness={avg_brightness:.1f}, std={std_dev:.1f}")
        return number

    def _is_revealed_cell(self, cell_image: np.ndarray, gray: np.ndarray) -> bool:
        """Check if cell is revealed (opened) or still covered.

        Key observation from the game variant:
        - Covered cells: center region is uniform color (std ≈ 0)
        - Revealed cells: center region has content (std > 0)

        Args:
            cell_image: BGR image of the cell
            gray: Grayscale image of the cell

        Returns:
            True if cell is revealed (opened), False if covered
        """
        h, w = gray.shape

        # Check center region (avoid border effects)
        margin_h = h // 4
        margin_w = w // 4
        center = gray[margin_h : h - margin_h, margin_w : w - margin_w]

        if center.size == 0:
            return False

        # Calculate center region statistics
        center_std = np.std(center)

        # Covered cells have uniform color in center (std ≈ 0)
        # Revealed cells have content (number or symbol) which creates variation (std > 0)
        # Use threshold to account for minor noise
        return center_std > 10

    def _has_white_border(self, gray: np.ndarray, h: int, w: int) -> bool:
        """Check if cell has white border (indicates revealed cell).

        Args:
            gray: Grayscale image of the cell
            h: Height
            w: Width

        Returns:
            True if white border detected
        """
        border_thickness = max(2, min(h, w) // 10)

        # Check edges for white pixels
        # Top edge
        top_edge = gray[:border_thickness, :]
        top_white_ratio = np.sum(top_edge > 180) / top_edge.size

        # Bottom edge
        bottom_edge = gray[-border_thickness:, :]
        bottom_white_ratio = np.sum(bottom_edge > 180) / bottom_edge.size

        # Left edge
        left_edge = gray[:, :border_thickness]
        left_white_ratio = np.sum(left_edge > 180) / left_edge.size

        # Right edge
        right_edge = gray[:, -border_thickness:]
        right_white_ratio = np.sum(right_edge > 180) / right_edge.size

        # If at least 3 edges have significant white pixels, it has a border
        edges_with_white = 0
        if top_white_ratio > 0.3:
            edges_with_white += 1
        if bottom_white_ratio > 0.3:
            edges_with_white += 1
        if left_white_ratio > 0.3:
            edges_with_white += 1
        if right_white_ratio > 0.3:
            edges_with_white += 1

        return edges_with_white >= 3

    def classify_board(self, cell_images: List[List[np.ndarray]], debug: bool = False) -> List[List[int]]:
        """Classify all cells in a board.

        Args:
            cell_images: 2D list of cell images
            debug: If True, print debug information for each cell

        Returns:
            2D list of cell states
        """
        board_state = []
        for r, row in enumerate(cell_images):
            row_state = []
            for c, cell in enumerate(row):
                if debug:
                    print(f"  Cell ({r},{c}):", end="")
                state = self.classify(cell, debug=debug)
                row_state.append(state)
            board_state.append(row_state)
        return board_state

    def _is_flag(self, cell_image: np.ndarray) -> bool:
        """Check if cell contains a flag.

        Flags typically have:
        - Red or yellow color
        - Pointed/triangular shape
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(cell_image, cv2.COLOR_BGR2HSV)

        # Red color range in HSV (red wraps around 180)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        # Yellow color range in HSV
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([35, 255, 255])

        # Create masks for red and yellow
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask_red1, mask_red2)
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # Combine red and yellow masks
        flag_mask = cv2.bitwise_or(red_mask, yellow_mask)

        # Count colored pixels
        color_ratio = np.sum(flag_mask > 0) / flag_mask.size

        # Flag cells have significant red or yellow content
        return color_ratio > 0.08

    def _is_covered(self, cell_image: np.ndarray) -> bool:
        """Check if cell is still covered (not revealed).

        Covered cells typically:
        - Are darker (deep gray in this variant)
        - Have more uniform color (no text)
        - May have 3D beveled appearance
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

        # Calculate average brightness
        avg_brightness = np.mean(gray)
        std_dev = np.std(gray)

        # In this variant:
        # - Covered cells: dark gray (brightness ~50-100), low std_dev
        # - Revealed cells: light gray (brightness ~150-200), may have text (higher std_dev)

        # Simple brightness threshold
        # Covered cells are typically darker than revealed cells
        if avg_brightness < 120 and std_dev < 40:
            return True

        # Check for 3D bevel effect (gradient at edges)
        h, w = gray.shape
        border_region = max(2, h // 10)

        # Sample edge and center regions
        top_edge = gray[:border_region, :]
        bottom_edge = gray[-border_region:, :]
        left_edge = gray[:, :border_region]
        right_edge = gray[:, -border_region:]

        center = gray[border_region:-border_region, border_region:-border_region]

        if center.size == 0:
            return True

        edge_avg = (np.mean(top_edge) + np.mean(bottom_edge) + np.mean(left_edge) + np.mean(right_edge)) / 4
        center_avg = np.mean(center)

        # Covered cells have a gradient (lighter edges, darker center for raised effect)
        has_bevel = edge_avg > center_avg + 8

        return has_bevel

    def _is_question_mark(self, cell_image: np.ndarray) -> bool:
        """Check if cell contains a question mark.

        Question mark cells are covered but have '?' displayed.
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

        # Threshold to get dark pixels (question mark is typically dark)
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

        # Look for the characteristic shape of '?'
        # It typically has a curved top part and a dot below

        # Count dark pixels
        dark_ratio = np.sum(binary > 0) / binary.size

        # Question mark has moderate dark pixel ratio
        return 0.05 < dark_ratio < 0.3

    def _is_mine(self, cell_image: np.ndarray) -> bool:
        """Check if cell contains a mine.

        Mines are typically:
        - Black circular shape (smaller than the cell)
        - With spikes radiating outward
        - Often on red background (if exploded)
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Check for black circular shape
        _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)

            if perimeter == 0:
                continue

            # Circularity: 4*pi*area/perimeter^2
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # Mine body is roughly circular (0.5-1.0)
            relative_area = area / (h * w)

            # IMPORTANT: A mine should be a small object in the center, not the entire cell
            # The entire cell being detected as circular is usually just the cell border
            # A real mine typically occupies 10-50% of the cell area
            if circularity > 0.5 and 0.05 < relative_area < 0.6:
                return True

        # Also check for exploded cell (red background)
        hsv = cv2.cvtColor(cell_image, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        red_ratio = np.sum(red_mask > 0) / red_mask.size

        if red_ratio > 0.5:  # Mostly red = exploded
            return True

        return False

    def _recognize_number(self, cell_image: np.ndarray, debug: bool = False) -> int:
        """Recognize the number in a revealed cell.

        Uses color-based recognition first (fast and reliable for minesweeper),
        falls back to OCR if available.

        Args:
            cell_image: BGR image of a revealed cell
            debug: If True, print debug information

        Returns:
            Number 0-8, or CELL_UNKNOWN if not recognized
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Resize to standard size for consistent analysis
        min_size = 32
        if h < min_size or w < min_size:
            scale = max(min_size / h, min_size / w)
            new_h, new_w = int(h * scale), int(w * scale)
            gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            cell_image = cv2.resize(cell_image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            h, w = gray.shape

        # Check if cell is mostly uniform (empty/zero)
        # Use center region to avoid border interference
        margin = max(2, h // 8)
        center = gray[margin:h - margin, margin:w - margin]
        std_dev = np.std(center)
        avg_brightness = np.mean(center)

        if debug:
            print(f"    std={std_dev:.1f}, avg_brightness={avg_brightness:.1f}")

        # Empty cells have very low standard deviation (uniform color)
        if std_dev < 12:
            if debug:
                print(f"    Empty cell (std={std_dev:.1f})")
            return 0

        # Try color-based recognition first (fast and reliable)
        number = self._recognize_by_color(cell_image, debug=debug)
        if number >= 0:
            return number

        # Try OCR recognition with multiple preprocessing strategies
        number = self._recognize_by_ocr(cell_image, gray, debug=debug)
        if number >= 0:
            return number

        if debug:
            print(f"    Failed to recognize number")
        return CELL_UNKNOWN

    def _recognize_by_color(self, cell_image: np.ndarray, debug: bool = False) -> int:
        """Recognize digit by analyzing the digit region shape.

        This game variant uses digits that can be either:
        - Bright on dark background
        - Or have contrast with background

        We use adaptive thresholding and shape analysis.

        Args:
            cell_image: BGR image of a cell
            debug: If True, print debug information

        Returns:
            Number 0-8, or -1 if not recognized
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Focus on center region to avoid border
        margin = max(2, h // 8)
        center = gray[margin:h - margin, margin:w - margin]

        # Use adaptive thresholding to find the digit
        # First, try to detect if digit is bright or dark
        center_mean = np.mean(center)
        center_std = np.std(center)

        if debug:
            print(f"    Center mean={center_mean:.1f}, std={center_std:.1f}")

        # Try different thresholding strategies
        # Strategy 1: Fixed threshold for bright pixels
        bright_mask = center > max(50, center_mean + center_std)

        # Strategy 2: Otsu's thresholding
        _, otsu_mask = cv2.threshold(center, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_mask = otsu_mask > 0

        # Strategy 3: Adaptive thresholding
        adaptive_mask = cv2.adaptiveThreshold(
            center, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        ) > 0

        # Use the mask that gives the most reasonable digit area
        masks = [
            ("bright", bright_mask),
            ("otsu", otsu_mask),
            ("adaptive", adaptive_mask),
        ]

        best_mask = None
        best_ratio = 0
        best_name = ""

        for name, mask in masks:
            count = np.sum(mask)
            ratio = count / mask.size
            # Good digit should occupy 5-50% of the cell
            if 0.05 < ratio < 0.5:
                if best_mask is None or abs(ratio - 0.2) < abs(best_ratio - 0.2):
                    best_mask = mask
                    best_ratio = ratio
                    best_name = name

        if best_mask is None:
            # Try inverted adaptive threshold
            inv_adaptive = cv2.adaptiveThreshold(
                center, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            ) > 0
            count = np.sum(inv_adaptive)
            ratio = count / inv_adaptive.size
            if 0.05 < ratio < 0.5:
                best_mask = inv_adaptive
                best_ratio = ratio
                best_name = "inv_adaptive"

        if best_mask is None:
            if debug:
                print(f"    No suitable mask found")
            return -1

        if debug:
            print(f"    Using mask: {best_name}, ratio: {best_ratio:.3f}")

        # Analyze the shape using contours
        digit_uint8 = (best_mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(digit_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return -1

        # Get the largest contour (should be the digit)
        largest_contour = max(contours, key=cv2.contourArea)
        digit_area = cv2.contourArea(largest_contour)

        if digit_area < 20:  # Too small
            return -1

        # Get bounding box
        x, y, bw, bh = cv2.boundingRect(largest_contour)
        aspect_ratio = bw / bh if bh > 0 else 0

        # Get contour moments for shape analysis
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return -1

        # Calculate shape features
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        solidity = digit_area / hull_area if hull_area > 0 else 0
        extent = digit_area / (bw * bh) if (bw * bh) > 0 else 0

        # Count "holes" in the digit
        contours_full, hierarchy = cv2.findContours(digit_uint8, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        holes = 0
        if hierarchy is not None:
            for i, h in enumerate(hierarchy[0]):
                if h[3] != -1:  # Has parent = inner contour
                    holes += 1

        if debug:
            print(f"    Digit area: {digit_area:.1f}, bbox: {bw}x{bh}, aspect: {aspect_ratio:.2f}")
            print(f"    Solidity: {solidity:.3f}, Extent: {extent:.3f}, Holes: {holes}")

        # Classification based on shape features

        # Digit 8: 2 holes
        if holes >= 2:
            if debug:
                print(f"    Detected: 8 (2 holes)")
            return 8

        # Digit 0: 1 hole, square-ish, high solidity
        if holes == 1 and aspect_ratio > 0.6 and aspect_ratio < 1.5 and solidity > 0.7:
            if debug:
                print(f"    Detected: 0 (1 hole, square-ish)")
            return 0

        # Digit 4: might have 1 hole, or be angular
        # Digit 6: 1 hole at top
        # Digit 9: 1 hole at bottom

        # For digits without holes (1, 2, 3, 5, 7)
        # Use shape features to distinguish

        # Digit 1: very thin, high aspect ratio (tall and narrow)
        if aspect_ratio < 0.5 and solidity > 0.6:
            if debug:
                print(f"    Detected: 1 (thin)")
            return 1

        # Digit 7: typically has a horizontal stroke at top
        # Low extent, angular

        # Digit 2: distinctive curve pattern
        # Analyze the upper and lower parts
        if holes == 0 and solidity < 0.55:
            # Check for "2" pattern
            # Divide into quadrants and analyze
            cx = x + bw // 2
            cy = y + bh // 2

            # Upper-left, upper-right, lower-left, lower-right
            ul = np.sum(best_mask[y:cy, x:cx]) if cy > y and cx > x else 0
            ur = np.sum(best_mask[y:cy, cx:x + bw]) if cy > y and x + bw > cx else 0
            ll = np.sum(best_mask[cy:y + bh, x:cx]) if y + bh > cy and cx > x else 0
            lr = np.sum(best_mask[cy:y + bh, cx:x + bw]) if y + bh > cy and x + bw > cx else 0

            total = ul + ur + ll + lr
            if total > 0:
                ul_ratio = ul / total
                ur_ratio = ur / total
                ll_ratio = ll / total
                lr_ratio = lr / total

                if debug:
                    print(f"    Quadrants: UL={ul_ratio:.2f}, UR={ur_ratio:.2f}, LL={ll_ratio:.2f}, LR={lr_ratio:.2f}")

                # Digit 2 pattern (observed from data):
                # LL is highest (~0.32), UR is second (~0.28), LR is third (~0.24), UL is lowest (~0.16)
                if ll_ratio > 0.25 and ll_ratio > ul_ratio and ur_ratio > ul_ratio:
                    if debug:
                        print(f"    Detected: 2 (quadrant pattern)")
                    return 2

        # Digit 3: right-heavy, no holes
        # Digit 5: left-heavy at bottom, right-heavy at top

        # Default: try to return a reasonable guess
        # If low solidity, might be 2, 3, 5, or 7
        # If high solidity, might be filled digit

        return -1

    def _recognize_by_ocr(self, cell_image: np.ndarray, gray: np.ndarray = None, debug: bool = False) -> int:
        """Recognize digit using Tesseract OCR with multiple preprocessing strategies.

        Args:
            cell_image: BGR image of a cell
            gray: Pre-computed grayscale image (optional)
            debug: If True, print debug information

        Returns:
            Number 0-8, or -1 if not recognized
        """
        try:
            import pytesseract

            if gray is None:
                gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

            h, w = gray.shape

            # Try multiple preprocessing strategies
            preprocessing_strategies = [
                self._preprocess_otsu,
                self._preprocess_adaptive,
                self._preprocess_color_based,
                self._preprocess_morphology,
            ]

            for strategy_idx, preprocess_func in enumerate(preprocessing_strategies):
                processed = preprocess_func(cell_image, gray)
                if processed is None:
                    continue

                # Add white border for better OCR
                border_size = max(5, h // 4)
                bordered = cv2.copyMakeBorder(
                    processed, border_size, border_size, border_size, border_size,
                    cv2.BORDER_CONSTANT, value=255
                )

                # Scale up for better OCR accuracy
                scale_factor = max(2, 64 // min(h, w))
                scaled = cv2.resize(
                    bordered, None, fx=scale_factor, fy=scale_factor,
                    interpolation=cv2.INTER_CUBIC
                )

                # Try multiple OCR configurations
                ocr_configs = [
                    "--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789",
                    "--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789",
                    "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789",
                    "--psm 13 --oem 3 -c tessedit_char_whitelist=0123456789",
                ]

                for config in ocr_configs:
                    try:
                        from PIL import Image
                        pil_img = Image.fromarray(scaled)
                        text = pytesseract.image_to_string(pil_img, config=config).strip()

                        if text:
                            # Clean up result
                            text = text.replace("O", "0").replace("o", "0")
                            text = text.replace("S", "5").replace("s", "5")
                            text = text.replace("B", "8").replace("b", "8")
                            text = text.replace("Z", "2").replace("z", "2")
                            text = text.replace("l", "1").replace("I", "1").replace("|", "1")

                            # Extract first digit
                            digits = [c for c in text if c.isdigit()]
                            if digits:
                                num = int(digits[0])
                                if 0 <= num <= 8:
                                    if debug:
                                        print(f"    OCR result: {num} (strategy={strategy_idx}, config={config.split()[0]})")
                                    return num
                    except Exception:
                        continue

        except ImportError:
            if debug:
                print("    pytesseract not installed")
        except Exception as e:
            if debug:
                print(f"    OCR error: {e}")

        return -1

    def _preprocess_otsu(self, cell_image: np.ndarray, gray: np.ndarray) -> np.ndarray:
        """Preprocess using Otsu's thresholding."""
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Ensure dark text on white background
        white_pixels = np.sum(binary == 255)
        black_pixels = np.sum(binary == 0)
        if black_pixels > white_pixels:
            binary = cv2.bitwise_not(binary)

        return binary

    def _preprocess_adaptive(self, cell_image: np.ndarray, gray: np.ndarray) -> np.ndarray:
        """Preprocess using adaptive thresholding."""
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Ensure dark text on white background
        white_pixels = np.sum(binary == 255)
        black_pixels = np.sum(binary == 0)
        if black_pixels > white_pixels:
            binary = cv2.bitwise_not(binary)

        return binary

    def _preprocess_color_based(self, cell_image: np.ndarray, gray: np.ndarray) -> np.ndarray:
        """Preprocess by extracting colored number regions."""
        # Numbers in minesweeper are typically colored (blue, green, red, etc.)
        hsv = cv2.cvtColor(cell_image, cv2.COLOR_BGR2HSV)

        # Create mask for colored pixels (high saturation)
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]

        # Colored pixels have high saturation and reasonable brightness
        color_mask = (saturation > 30) & (value > 50)

        # Create binary image: white background, colored pixels as black
        binary = np.ones_like(gray) * 255
        binary[color_mask] = 0

        return binary

    def _preprocess_morphology(self, cell_image: np.ndarray, gray: np.ndarray) -> np.ndarray:
        """Preprocess with morphological operations."""
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Otsu threshold
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Ensure dark text on white background
        white_pixels = np.sum(binary == 255)
        black_pixels = np.sum(binary == 0)
        if black_pixels > white_pixels:
            binary = cv2.bitwise_not(binary)

        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        return binary
