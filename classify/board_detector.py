"""Board detection module for automatically detecting grid dimensions."""

from typing import Tuple, Optional, List

import cv2
import numpy as np


class BoardDetector:
    """Detects minesweeper board grid structure from image."""

    def __init__(self, image: np.ndarray):
        """Initialize detector with an image.

        Args:
            image: BGR image of the minesweeper board region
        """
        self.image = image
        self.gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.rows = 0
        self.cols = 0
        self.cell_width = 0
        self.cell_height = 0
        self.grid_origin = (0, 0)

    def detect_grid(self) -> Tuple[int, int]:
        """Detect the grid dimensions (rows x cols) automatically.

        Returns:
            Tuple of (rows, cols)
        """
        # Try contour-based detection first
        result = self._detect_by_contours()
        if result:
            self.rows, self.cols = result
            return result

        # Fallback to line-based detection
        result = self._detect_by_lines()
        if result:
            self.rows, self.cols = result
            return result

        # Fallback to uniform grid assumption
        result = self._detect_by_uniform_cells()
        if result:
            self.rows, self.cols = result
            return result

        return (0, 0)

    def _detect_by_contours(self) -> Optional[Tuple[int, int]]:
        """Detect grid by finding cell contours.

        This method finds cell-like shapes and counts them.
        """
        # Apply adaptive thresholding for robust cell detection
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)

        # Try both threshold methods
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Filter contours by aspect ratio and size
        h, w = self.gray.shape
        min_area = (w * h) / 1000  # Minimum cell area
        max_area = (w * h) / 4  # Maximum cell area

        cell_boxes = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            area = bw * bh
            aspect = bw / bh if bh > 0 else 0

            # Cells should be roughly square and reasonable size
            if min_area < area < max_area and 0.5 < aspect < 2.0:
                cell_boxes.append((x, y, bw, bh))

        if len(cell_boxes) < 4:  # Need at least 2x2 grid
            return None

        # Cluster cells by row and column positions
        rows, cols, cell_w, cell_h, origin = self._cluster_cells(cell_boxes)

        if rows > 0 and cols > 0:
            self.cell_width = cell_w
            self.cell_height = cell_h
            self.grid_origin = origin
            return (rows, cols)

        return None

    def _cluster_cells(self, cell_boxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int, Tuple[int, int]]:
        """Cluster cell boxes into rows and columns.

        Returns:
            Tuple of (rows, cols, cell_width, cell_height, origin)
        """
        if not cell_boxes:
            return (0, 0, 0, 0, (0, 0))

        # Get average cell dimensions
        avg_width = int(np.mean([b[2] for b in cell_boxes]))
        avg_height = int(np.mean([b[3] for b in cell_boxes]))

        # Get cell centers
        centers = [(x + w // 2, y + h // 2) for x, y, w, h in cell_boxes]

        # Cluster by y-coordinate for rows
        y_coords = sorted(set(c[1] for c in centers))
        row_positions = self._cluster_1d(y_coords, tolerance=avg_height // 2)

        # Cluster by x-coordinate for columns
        x_coords = sorted(set(c[0] for c in centers))
        col_positions = self._cluster_1d(x_coords, tolerance=avg_width // 2)

        rows = len(row_positions)
        cols = len(col_positions)

        # Calculate origin (top-left of grid)
        if row_positions and col_positions:
            origin_x = min(col_positions) - avg_width // 2
            origin_y = min(row_positions) - avg_height // 2
            origin = (max(0, origin_x), max(0, origin_y))
        else:
            origin = (0, 0)

        return (rows, cols, avg_width, avg_height, origin)

    def _cluster_1d(self, positions: List[int], tolerance: int) -> List[int]:
        """Cluster 1D positions into groups.

        Args:
            positions: Sorted list of positions
            tolerance: Maximum distance to consider same group

        Returns:
            List of cluster centers
        """
        if not positions:
            return []

        clusters = []
        current_cluster = [positions[0]]

        for pos in positions[1:]:
            if pos - current_cluster[-1] <= tolerance:
                current_cluster.append(pos)
            else:
                # Finish current cluster
                clusters.append(int(np.mean(current_cluster)))
                current_cluster = [pos]

        # Don't forget the last cluster
        clusters.append(int(np.mean(current_cluster)))

        return clusters

    def _detect_by_lines(self) -> Optional[Tuple[int, int]]:
        """Detect grid by finding horizontal and vertical lines.

        Uses Hough line transform to detect grid lines.
        """
        # Edge detection
        edges = cv2.Canny(self.gray, 50, 150, apertureSize=3)

        # Hough line transform
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=50,
            minLineLength=min(self.gray.shape) // 4,
            maxLineGap=10,
        )

        if lines is None or len(lines) < 4:
            return None

        # Separate horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x2 - x1) > abs(y2 - y1):
                # Horizontal line
                horizontal_lines.append((y1 + y2) // 2)
            else:
                # Vertical line
                vertical_lines.append((x1 + x2) // 2)

        if len(horizontal_lines) < 2 or len(vertical_lines) < 2:
            return None

        # Cluster lines
        tolerance = min(self.gray.shape) // 20
        row_lines = self._cluster_1d(sorted(horizontal_lines), tolerance)
        col_lines = self._cluster_1d(sorted(vertical_lines), tolerance)

        # Number of cells = number of lines - 1
        rows = len(row_lines) - 1
        cols = len(col_lines) - 1

        if rows > 0 and cols > 0:
            # Calculate cell dimensions
            if len(row_lines) >= 2:
                self.cell_height = row_lines[1] - row_lines[0]
            if len(col_lines) >= 2:
                self.cell_width = col_lines[1] - col_lines[0]
            self.grid_origin = (col_lines[0], row_lines[0])
            return (rows, cols)

        return None

    def _detect_by_uniform_cells(self) -> Optional[Tuple[int, int]]:
        """Detect grid assuming uniform cell sizes.

        This is a fallback that assumes square cells.
        """
        h, w = self.gray.shape

        # Assume cells are roughly square
        # Try common grid sizes and find best fit
        best_size = None
        best_score = 0

        for cell_size in range(20, min(h, w) // 2, 2):
            rows = h // cell_size
            cols = w // cell_size

            if rows < 2 or cols < 2:
                continue

            # Score based on how well the grid fits
            row_remainder = h % cell_size
            col_remainder = w % cell_size

            # Prefer grids that fill most of the image
            fit_score = (h - row_remainder) / h + (w - col_remainder) / w

            # Check for consistent cell colors at grid positions
            consistency_score = self._check_grid_consistency(cell_size)

            total_score = fit_score + consistency_score

            if total_score > best_score:
                best_score = total_score
                best_size = cell_size

        if best_size:
            self.cell_width = best_size
            self.cell_height = best_size
            self.rows = h // best_size
            self.cols = w // best_size
            self.grid_origin = (0, 0)
            return (self.rows, self.cols)

        return None

    def _check_grid_consistency(self, cell_size: int) -> float:
        """Check color consistency at grid intersections.

        Returns:
            Consistency score (0-1)
        """
        h, w = self.gray.shape
        consistency = 0
        count = 0

        for y in range(0, h - cell_size, cell_size):
            for x in range(0, w - cell_size, cell_size):
                # Sample corners and center of cell
                cell = self.gray[y : y + cell_size, x : x + cell_size]
                if cell.size == 0:
                    continue

                # Check that cell has consistent color
                std = np.std(cell)
                consistency += 1 - min(std / 128, 1)
                count += 1

        return consistency / max(count, 1)

    def get_cell_positions(self) -> List[Tuple[int, int, int, int]]:
        """Get the position of each cell in the grid.

        Returns:
            List of (x, y, width, height) for each cell
        """
        positions = []
        ox, oy = self.grid_origin

        for row in range(self.rows):
            for col in range(self.cols):
                x = ox + col * self.cell_width
                y = oy + row * self.cell_height
                positions.append((x, y, self.cell_width, self.cell_height))

        return positions

    def get_cell_images(self) -> List[List[np.ndarray]]:
        """Extract individual cell images from the board.

        Returns:
            2D list of cell images (BGR format)
        """
        cells = []
        ox, oy = self.grid_origin

        for row in range(self.rows):
            row_cells = []
            for col in range(self.cols):
                x = ox + col * self.cell_width
                y = oy + row * self.cell_height

                cell_img = self.image[y : y + self.cell_height, x : x + self.cell_width]
                row_cells.append(cell_img.copy())
            cells.append(row_cells)

        return cells

    def get_grid_info(self) -> dict:
        """Get grid information.

        Returns:
            Dictionary with rows, cols, cell_width, cell_height, origin
        """
        return {
            "rows": self.rows,
            "cols": self.cols,
            "cell_width": self.cell_width,
            "cell_height": self.cell_height,
            "origin": self.grid_origin,
        }
