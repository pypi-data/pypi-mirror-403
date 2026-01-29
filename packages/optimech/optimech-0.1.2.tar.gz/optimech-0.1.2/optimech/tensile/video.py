import cv2
import os


def extract_frames(video_path, output_dir, fps=None):
    """
    Extract frames from a video file.

    Parameters
    ----------
    video_path : str
        Path to the video file.
    output_dir : str
        Directory where frames will be saved.
    fps : int or None
        Desired output frame rate.

    Returns
    -------
    float
        Effective frame rate of extracted frames.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    # Get the fps
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = 1 if fps is None else int(round(video_fps / fps))

    frame_id = 0
    saved_id = 0

    # Frame obtention
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_id % frame_interval == 0:
            fname = f"frame-{saved_id:04d}.tif"
            cv2.imwrite(os.path.join(output_dir, fname), frame)
            saved_id += 1

        frame_id += 1

    cap.release()
    return video_fps if fps is None else fps
