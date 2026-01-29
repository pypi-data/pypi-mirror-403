import os
import numpy as np

from .video import extract_frames
from .tracking import track_gauge_distance_px
from .io import save_tensile_csv
from .vision import crop_images


def analyze(
    gauge_length_mm: float,
    video_path: str | None = None,
    image_dir: str | None = None,
    fps: int | None = None,
    threshold_gray: int = 80,
    line_threshold_factor: float = 0.2,
    workdir: str = "tensile_output",
    output_csv: str | None = None,
    # --- CROP PARAMETERS ---
    crop: bool = True,
    crop_x_ratio: tuple[float, float] = (0.43, 0.45),
    crop_y_ratio: tuple[float, float] = (0.40, 0.67),
):

    """
    Perform optical extensometry analysis from a tensile test video
    or from a directory of images.

    This function:
    1) Extracts frames from a video (optional)
    2) Tracks the pixel distance between extensometer lines
    3) Converts pixel distances to physical elongation and strain
    4) Optionally saves the results to a CSV file

    Parameters
    ----------
    gauge_length_mm : float
        Initial gauge length of the extensometer [mm].
    video_path : str or None
        Path to the tensile test video.
    image_dir : str or None
        Directory containing image frames.
    fps : int or None
        Frames per second to extract from the video.
    threshold_gray : int
        Grayscale threshold used to detect black lines.
    line_threshold_factor : float
        Minimum fraction of black pixels per row to classify a line.
    workdir : str
        Working directory for intermediate outputs.
    output_csv : str or None
        Path to save the output CSV file.

    Returns
    -------
    dict
        Dictionary containing time, elongation, strain and tracking data.
    """

    print("Analysis of tensile test started!")

    # ---------------------------------------------------------
    # 1) Acquire images (video → frames if needed)
    # ---------------------------------------------------------
    if video_path is not None:
        frames_dir = os.path.join(workdir, "frames")
        extract_frames(video_path, frames_dir, fps=fps)
        image_dir = frames_dir

    if image_dir is None:
        raise ValueError("Either video_path or image_dir must be provided")

    # ---------------------------------------------------------
    # 2) Optional cropping of extensometer region
    # ---------------------------------------------------------
    if crop:
        cropped_dir = os.path.join(workdir, "cropped")
        crop_images(
            input_dir=image_dir,
            output_dir=cropped_dir,
            x_ratio=crop_x_ratio,
            y_ratio=crop_y_ratio,
        )
        image_dir = cropped_dir


    # ---------------------------------------------------------
    # 3) Track extensometer distance in pixels
    # ---------------------------------------------------------
    (
        distances_px,
        top_lines,
        bottom_lines,
        images_rgb,
    ) = track_gauge_distance_px(
        image_dir,
        threshold_gray,
        line_threshold_factor,
    )

    # ---------------------------------------------------------
    # 4) Convert pixel distance to physical units
    # ---------------------------------------------------------
    px0 = distances_px[0]                # initial gauge length in pixels
    mm_per_px = gauge_length_mm / px0    # calibration factor

    elongation_mm = (distances_px - px0) * mm_per_px
    strain = elongation_mm / gauge_length_mm
    
    if fps is None:
        # if fps is unknown, assume 1 frame = 1 s
        time_s = np.arange(len(distances_px))
    else:
        time_s = np.arange(len(distances_px)) / fps

    # ---------------------------------------------------------
    # 5) Save results (optional)
    # ---------------------------------------------------------
    if output_csv is not None:
        save_tensile_csv(
            time_s,
            distances_px,
            elongation_mm,
            strain,
            output_csv,
            workdir,
        )

    # ---------------------------------------------------------
    # 6) Return all relevant results
    # ---------------------------------------------------------
    return {
        "time_s": time_s,
        "elongation_mm": elongation_mm,
        "strain": strain,
        "mm_per_pixel": mm_per_px,
        "distance_px": distances_px,
        "top_lines": top_lines,
        "bottom_lines": bottom_lines,
        "images_rgb": images_rgb,
    }
