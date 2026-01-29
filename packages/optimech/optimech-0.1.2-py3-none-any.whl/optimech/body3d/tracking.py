import os
import cv2
import numpy as np

from .vision import detect_contours, compute_reference_point


def find_tracked_point(external_contour, y_ref):
    """
    Find the contact (tracked) point in a frame using the external contour
    and a reference vertical position.

    Parameters
    ----------
    external_contour : np.ndarray
        External contour of the object, as returned by OpenCV
        (shape: [N, 1, 2], with x-y pixel coordinates).
    y_ref : float
        Reference vertical position [px] used to locate the closest
        contour point (e.g. expected contact height).

    Returns
    -------
    tracked_point : tuple of int or None
        (x, y) pixel coordinates of the tracked point if found.
        Returns None if no suitable contour points exist on the right side.
    """
        
    pts = external_contour[:, 0, :]
    x_mid = (pts[:, 0].min() + pts[:, 0].max()) / 2

    right_pts = pts[pts[:, 0] >= x_mid]
    if len(right_pts) == 0:
        return None

    idx = np.argmin(np.abs(right_pts[:, 1] - y_ref))
    return tuple(map(int, right_pts[idx]))


def track_displacement_px(frames_dir: str):
    """
        Track the horizontal displacement of a reference point across
        a sequence of image frames.

        Parameters
        ----------
        frames_dir : str
            Directory containing the image frames to process. Supported
            formats include PNG, JPG, JPEG and TIF.

        Returns
        -------
        displacement : list of float
            Horizontal displacement [px] for each frame, computed as
            (x_ref - x_current). NaN is returned for frames where the
            contour or tracked point cannot be determined.
        reference_point : tuple of float
            Initial reference point (x_ref, y_ref) in pixel coordinates,
            computed from the first frame.
        tracked_points : list of tuple or None
            Tracked (x, y) pixel coordinates for each frame. Entries are
            None when tracking fails.
        """

    
    # Collect and sort image frames
    frame_files = sorted([
        f for f in os.listdir(frames_dir)
        if f.lower().endswith((".png", ".jpg", ".tif"))
    ])

    if len(frame_files) < 2:
        raise ValueError("Not enough frames")
    
    # Load first frame to compute reference point
    first = os.path.join(frames_dir, frame_files[0])
    img0 = cv2.imread(first)

    contours, hierarchy = detect_contours(first)
    x_ref, y_ref = compute_reference_point(contours, hierarchy, img0.shape)

    displacement = []
    tracked_points = []


    # Process each frame independently
    for fname in frame_files:
        path = os.path.join(frames_dir, fname)
        contours, hierarchy = detect_contours(path)

        # Extract only external contours
        externals = [
            contours[i] for i in range(len(contours))
            if hierarchy[0][i][3] == -1
        ]

        if not externals:
            displacement.append(np.nan)
            tracked_points.append(None)
            continue

        # Select the largest external contour (specimen)
        ext = max(externals, key=cv2.contourArea)
        tracked = find_tracked_point(ext, y_ref)

        if tracked is None:
            displacement.append(np.nan)
            tracked_points.append(None)
            continue

        # Compute horizontal displacement relative to reference
        x_now, _ = tracked
        displacement.append(x_ref - x_now)
        tracked_points.append(tracked)

    return displacement, (x_ref, y_ref), tracked_points
