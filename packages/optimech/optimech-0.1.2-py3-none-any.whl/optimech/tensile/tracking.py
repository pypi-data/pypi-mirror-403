import os
import cv2
import numpy as np

from .vision import detect_extensometer_lines


def track_gauge_distance_px(
    image_dir: str,
    threshold_gray: int,
    line_threshold_factor: float
):
    """
    Track the pixel distance between extensometer lines
    for a sequence of images.

    Parameters
    ----------
    image_dir : str
        Directory containing image frames.
    threshold_gray : int
        Grayscale threshold for black line detection.
    line_threshold_factor : float
        Minimum fraction of black pixels per row.

    Returns
    -------
    distances_px : np.ndarray
        Pixel distance between top and bottom lines.
    top_lines : np.ndarray
        Vertical position of the top line [px].
    bottom_lines : np.ndarray
        Vertical position of the bottom line [px].
    images_rgb : list
        RGB images for visualization.
    """

    # Collect and sort image files
    image_files = sorted([
        f for f in os.listdir(image_dir)
        if f.lower().endswith((".png", ".jpg", ".tif", ".jpeg"))
    ])

    distances_px = []
    top_lines = []
    bottom_lines = []
    images_rgb = []


    # Process each frame independently
    for fname in image_files:
        img = cv2.imread(os.path.join(image_dir, fname))

        if img is None:
            distances_px.append(np.nan)
            top_lines.append(np.nan)
            bottom_lines.append(np.nan)
            continue
        
        # Binarization
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        images_rgb.append(img_rgb)
        
        # Detection of black lines
        top, bottom = detect_extensometer_lines(
            img,
            threshold_gray,
            line_threshold_factor
        )

        top_lines.append(top)
        bottom_lines.append(bottom)

        if np.isnan(top) or np.isnan(bottom):
            distances_px.append(np.nan)
        else:
            distances_px.append(bottom - top)

    return (
        np.array(distances_px),
        np.array(top_lines),
        np.array(bottom_lines),
        images_rgb,
    )
