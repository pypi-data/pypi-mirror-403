import os
import cv2
import pandas as pd
import matplotlib.pyplot as plt
import imageio


def plot_displacement_vs_time(csv_path, workdir):
    """
    Plot displacement versus time from a displacement CSV file.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file containing displacement results.
        The file must include at least the columns:
        ["time_s", "elongation_mm"].
    workdir : str
        Directory where the output plot image will be saved.

    Returns
    -------
    None
        The function saves the plot to disk and displays it.
    """

    filename="disp_vs_time.png"

    os.makedirs(workdir, exist_ok=True)
    save_path = os.path.join(workdir, filename)

    df = pd.read_csv(csv_path)

    plt.figure(figsize=(8, 5))
    plt.plot(df["time_s"], df["elongation_mm"], lw=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Displacement (mm)")
    plt.title("Displacement vs Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()

    print("Displacement vs Time plot saved in body3d_output")


def make_tracking_gif(
    frames_dir,
    csv_path,
    ref_point,
    workdir,
    output_gif="tracking.gif",
    fps=60
):
    """
    Create an animated GIF showing the tracked displacement over image frames.

    Parameters
    ----------
    frames_dir : str
        Directory containing the image frames used for tracking.
    csv_path : str
        Path to the CSV file containing displacement results.
        Must include the column "distance_px".
    ref_point : tuple of int
        Fixed reference point (x_ref, y_ref) in pixel coordinates.
    workdir : str
        Directory where the output GIF will be saved.
    output_gif : str, optional
        Name of the output GIF file (default is "tracking.gif").
    fps : int, optional
        Frames per second for the GIF animation (default is 60).

    Returns
    -------
    output_path : str
        Path to the generated GIF file.
    """

    
    os.makedirs(workdir, exist_ok=True)
    output_path = os.path.join(workdir, output_gif)

    df = pd.read_csv(csv_path)
    frame_files = sorted(os.listdir(frames_dir))

    x_ref, y_ref = ref_point
    frames = []

    # Loop through the frames
    for i, fname in enumerate(frame_files):
        if i >= len(df):
            break
        row = df.iloc[i]
        if pd.isna(row["distance_px"]):
            continue

        img = cv2.imread(os.path.join(frames_dir, fname))
        x_now = int(x_ref - row["distance_px"])

        # Draw reference point (red), tracked point (yellow), and displacement vector
        cv2.circle(img, (x_ref, y_ref), 6, (0, 0, 255), -1)
        cv2.circle(img, (x_now, y_ref), 6, (0, 255, 255), -1)
        cv2.line(img, (x_ref, y_ref), (x_now, y_ref), (0, 255, 255), 2)

        frames.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    imageio.mimsave(output_path, frames, fps=fps)

    print("Displacement gif saved in body3d_plots")

    return output_path

def save_first_frame_with_contours(image_path, contours_external, contours_internal, workdir):
    """
    Save an image with external and internal contours overlaid.

    Parameters
    ----------
    image_path : str
        Path to the image file on which contours will be drawn.
    contours_external : np.ndarray
        External contour of the specimen (OpenCV contour format).
    contours_internal : np.ndarray
        Internal contour (e.g. inner cavity or contact region).
    workdir : str
        Directory where the output image will be saved.

    Returns
    -------
    save_path : str
        Path to the saved image containing the overlaid contours.
    """

    os.makedirs(workdir, exist_ok=True)
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    img_copy = img.copy()

    # External contour in green, internal contour in blue
    cv2.drawContours(img_copy, [contours_external], -1, (0, 255, 0), 2)  # external green
    cv2.drawContours(img_copy, [contours_internal], -1, (255, 0, 0), 2)  # internal blue

    save_path = os.path.join(workdir, "last_frame_contours.png")
    cv2.imwrite(save_path, img_copy)

    print("Last frame body 3d external and internal contours image saved in body3d_contours")

    return save_path