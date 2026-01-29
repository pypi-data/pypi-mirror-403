import cv2
import numpy as np


def detect_contours(image_path: str):
    """
    Detect red contours in an image using HSV thresholding.

    Parameters
    -------
    image path: str
        Directory of the selected image to detect contours on.

    Returns
    -------
    contours : list[np.ndarray]
    hierarchy : np.ndarray
    """

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # HSV scalling of the image
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower1 = np.array([0, 70, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([170, 70, 50])
    upper2 = np.array([180, 255, 255])

    # Red mask
    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find red contours using the mask
    contours, hierarchy = cv2.findContours(
        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    if hierarchy is None or len(contours) == 0:
        raise ValueError("No contours detected")

    return contours, hierarchy


def compute_reference_point(contours, hierarchy, image_shape):
    """
    Compute a fixed reference point from contours.

    Parameters
    ----------
    contours : list of np.ndarray
        List of contours detected in the image, as returned by OpenCV.
        Each contour has shape [N, 1, 2].
    hierarchy : np.ndarray
        Contour hierarchy array returned by OpenCV, used to distinguish
        external and internal contours.
    image_shape : tuple
        Shape of the image (height, width, channels), used to determine
        the right half of the image.

    Returns
    -------
    reference_point : tuple of int
        (x_ref, y_ref) pixel coordinates of the reference point.
    """

    # Obtention of the external and internal contours
    external = [
        contours[i] for i in range(len(contours))
        if hierarchy[0][i][3] == -1
    ]
    internal = [
        contours[i] for i in range(len(contours))
        if hierarchy[0][i][3] != -1
    ]

    if not external or not internal:
        raise ValueError("External or internal contour missing")
    
    # Select the largest external contour (specimen)
    ext = max(external, key=cv2.contourArea)
    intc = max(internal, key=cv2.contourArea)

    # Mean height of the body 3d (where contact happens)
    ys = intc[:, 0, 1]
    y_ref = int((ys.min() + ys.max()) / 2)

    # Mask of the right wall, as the contact point is on the external contour but on the RIGHT wall
    pts = ext[:, 0, :]
    h, w = image_shape[:2]
    right_pts = pts[pts[:, 0] > w // 2]

    # Point closer to the mean height that belongs in the right wall of the external contour
    idx = np.argmin(np.abs(right_pts[:, 1] - y_ref))
    x_ref = int(right_pts[idx, 0])

    print("Contact point calculated")

    return x_ref, y_ref
