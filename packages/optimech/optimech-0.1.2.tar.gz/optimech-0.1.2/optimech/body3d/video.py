import cv2
import os


def extract_frames(
    video_path: str,
    output_dir: str,
    fps: int,
    rotate_180: bool = False,
) -> float:
    """
    Extract frames from a video file.

    Parameters
    ----------
    video_path : str
        Path to the video file.
    output_dir : str
        Directory where frames will be saved.
    fps : int or None
        Desired frames per second. If None, extract all frames.
    rotate_180 : bool
        Rotate frames by 180 degrees (useful for smartphone recordings).

    Returns
    -------
    actual_fps : float
        Frames per second used for extraction.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Opne video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    frame_interval = 1
    frame_id = 0
    saved_id = 0

    # Ontention of the frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % frame_interval == 0:
            if rotate_180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)

            fname = f"frame-{saved_id:04d}.tif"
            cv2.imwrite(os.path.join(output_dir, fname), frame)
            saved_id += 1

        frame_id += 1

    cap.release()

    print("Video frames saved to body3d_output/frames")

    return fps
