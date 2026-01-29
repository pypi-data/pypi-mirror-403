import os
import cv2

from .video import extract_frames
from .tracking import track_displacement_px
from .vision import detect_contours
from .io import save_displacement_csv
from .visualization import save_first_frame_with_contours


def analyze(
    video_path: str,
    specimen_height_mm: float,
    workdir: str = "body3d_output",
    fps: int = 60,
):
    """
    Perform full optical displacement analysis of a body 3D test video.

    This is the main high-level pipeline that:
    1) Extracts frames from the input video,
    2) Tracks horizontal displacement in pixel coordinates,
    3) Computes a pixel-to-millimeter scale from specimen geometry,
    4) Saves full and relative displacement CSV files,
    5) Stores reference visual outputs for validation.

    Parameters
    ----------
    video_path : str
        Path to the input video file of the body 3D test.
    specimen_height_mm : float
        Physical height of the specimen [mm], used to convert
        pixel measurements to millimeters.
    workdir : str, optional
        Working directory where all outputs will be stored
        (default is "body3d_output").
    fps : int, optional
        Target frames per second for frame extraction
        (default is 60).

    Returns
    -------
    results : dict
        Dictionary containing:
        - "frames_dir" : str
            Directory containing extracted frames.
        - "csv_full" : str
            Path to the full displacement CSV file.
        - "csv_relative" : str
            Path to the filtered (relative) displacement CSV file.
        - "reference_point" : tuple of int
            Fixed reference point (x_ref, y_ref) in pixel coordinates.
        - "fps" : float
            Actual frames per second used in the analysis.
    """

    print("Analysis of body 3d test started!")

    os.makedirs(workdir, exist_ok=True)

    frames_dir = os.path.join(workdir, "frames")
    csv_full = os.path.join(workdir, "displacement_full.csv")
    csv_rel = os.path.join(workdir, "displacement_relative.csv")

    # ------------------------------------------------------------
    # 1) Extract frames from video
    # ------------------------------------------------------------
    actual_fps = extract_frames(video_path, frames_dir, fps=fps)

    # ------------------------------------------------------------
    # 2) Track displacement in pixel coordinates
    # ------------------------------------------------------------
    displacement_px, ref_point, tracked_pts = track_displacement_px(frames_dir)

    # ------------------------------------------------------------
    # 3) Compute px → mm scale from last frame geometry
    # ------------------------------------------------------------
    frame_files = sorted(os.listdir(frames_dir))
    last_frame = os.path.join(frames_dir, frame_files[-1])

    contours, hierarchy = detect_contours(last_frame)

    external = max(
        [contours[i] for i in range(len(contours)) if hierarchy[0][i][3] == -1],
        key=cv2.contourArea
    )

    internal = max(
        [contours[i] for i in range(len(contours)) if hierarchy[0][i][3] != -1],
        key=cv2.contourArea
    )

    # Save validation image with detected contours
    save_first_frame_with_contours(
        last_frame,
        external,
        internal,
        "body_3d_contours",
    )

    ys = external[:, 0, 1]
    height_px = ys.max() - ys.min()
    mm_per_px = specimen_height_mm / height_px

    # ------------------------------------------------------------
    # 4) Build time vector and save CSV outputs
    # ------------------------------------------------------------
    times = [i / actual_fps for i in range(len(displacement_px))]

    save_displacement_csv(
        times,
        displacement_px,
        mm_per_px,
        csv_full,
        csv_rel
    )

    return {
        "frames_dir": frames_dir,
        "csv_full": csv_full,
        "csv_relative": csv_rel,
        "reference_point": ref_point,
        "fps": actual_fps,
    }
