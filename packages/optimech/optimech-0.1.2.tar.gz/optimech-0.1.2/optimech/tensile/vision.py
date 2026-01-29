import cv2
import numpy as np
import os
from typing import Tuple, Optional


# ==========================================================
# 1) LOW-LEVEL IMAGE ANALYSIS
#    Detection of horizontal black extensometer lines
# ==========================================================

def find_black_line_rows(
    gray: np.ndarray,
    threshold_gray: int,
    line_threshold_factor: float
) -> np.ndarray:
    """
    Detect image rows that contain a significant amount of black pixels.
    These rows are assumed to correspond to horizontal extensometer lines.

    Parameters
    ----------
    gray : np.ndarray
        Grayscale version of the image.
    threshold_gray : int
        Pixel intensity threshold below which a pixel is considered black.
    line_threshold_factor : float
        Fraction of black pixels required in a row to classify it as a line.

    Returns
    -------
    np.ndarray
        Indices of image rows likely belonging to extensometer lines.
    """

    # Binary mask: 1 for black pixels, 0 otherwise
    binary = (gray < threshold_gray).astype(np.uint8)

    # Count black pixels per row
    row_sum = binary.sum(axis=1)

    # Threshold in number of pixels
    threshold = line_threshold_factor * binary.shape[1]

    return np.where(row_sum > threshold)[0]


def extract_top_bottom_lines(
    line_rows: np.ndarray
) -> tuple[Optional[float], Optional[float]]:
    """
    From detected line rows, extract the vertical position of the
    top and bottom extensometer lines.

    Parameters
    ----------
    line_rows : np.ndarray
        Row indices corresponding to detected black lines.

    Returns
    -------
    top_line : float or np.nan
        Vertical position of the top extensometer line [px].
    bottom_line : float or np.nan
        Vertical position of the bottom extensometer line [px].
    """

    if len(line_rows) == 0:
        return np.nan, np.nan

    # Group contiguous rows into blocks
    blocks = np.split(
        line_rows,
        np.where(np.diff(line_rows) > 1)[0] + 1
    )

    # Use first and last block as top and bottom lines
    if len(blocks) >= 2:
        top_line = np.mean(blocks[0])
        bottom_line = np.mean(blocks[-1])
    else:
        top_line = bottom_line = np.mean(blocks[0])

    return float(top_line), float(bottom_line)


def detect_extensometer_lines(
    img: np.ndarray,
    threshold_gray: int,
    line_threshold_factor: float
):
    """
    Detect the vertical pixel positions of the top and bottom
    extensometer lines in a single image.

    Parameters
    ----------
    img : np.ndarray
        Input image in BGR format (OpenCV default).
    threshold_gray : int
        Grayscale threshold for black line detection.
    line_threshold_factor : float
        Minimum black pixel fraction per row.

    Returns
    -------
    top_line : float
    bottom_line : float
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    line_rows = find_black_line_rows(
        gray,
        threshold_gray,
        line_threshold_factor
    )

    return extract_top_bottom_lines(line_rows)


# ==========================================================
# 2) IMAGE CROPPING (REGION OF INTEREST)
# ==========================================================

def crop_images(
    input_dir: str,
    output_dir: str,
    x_ratio: Tuple[float, float],
    y_ratio: Tuple[float, float]
):
    """
    Crop the extensometer region from all images in a directory.

    The crop window is defined using relative coordinates so that
    it is independent of image resolution.

    Parameters
    ----------
    input_dir : str
        Directory containing the original images.
    output_dir : str
        Directory where cropped images will be saved.
    x_ratio : tuple(float, float)
        Horizontal crop window expressed as fractions of image width.
        Example: (0.43, 0.45)
    y_ratio : tuple(float, float)
        Vertical crop window expressed as fractions of image height.
        Example: (0.40, 0.67)
    """

    # Create output directory if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    # Loop through all images
    for filename in sorted(os.listdir(input_dir)):
        input_path = os.path.join(input_dir, filename)

        img = cv2.imread(input_path)
        if img is None:
            continue

        h, w = img.shape[:2]

        # Convert relative ratios to absolute pixel coordinates
        x1 = int(w * x_ratio[0])
        x2 = int(w * x_ratio[1])
        y1 = int(h * y_ratio[0])
        y2 = int(h * y_ratio[1])

        cropped = img[y1:y2, x1:x2]

        cv2.imwrite(os.path.join(output_dir, filename), cropped)
    print("Tensile test images cropped and saved in tensile_output/cropped")
