import pandas as pd
import numpy as np

def save_displacement_csv(
    times,
    displacement_px,
    mm_per_px,
    output_full,
    output_relative
):
    """
    Save displacement results to CSV files in pixel and physical units.

    This function generates two CSV files:
    1) A full CSV containing time, pixel displacement and converted
       displacement in millimeters.
    2) A relative CSV trimmed to the interval where displacement changes
       occur, with time re-referenced so that the first significant
       displacement corresponds to t = 0.

    Parameters
    ----------
    times : array-like
        Time values [s] corresponding to each frame.
    displacement_px : array-like
        Horizontal displacement values [px] for each frame. NaN values
        are allowed and will be preserved in the output.
    mm_per_px : float
        Conversion factor from pixels to millimeters.
    output_full : str
        Path to the output CSV file containing the full time history.
    output_relative : str
        Path to the output CSV file containing the trimmed and
        time-shifted displacement history.

    Returns
    -------
    None
        The function writes CSV files to disk and does not return
        any value.
    """

    # ======================================================
    # 1) Save CSV
    # ======================================================
    rows = []
    for t, d in zip(times, displacement_px):
        if np.isnan(d):
            rows.append((round(t,5), np.nan, np.nan))
        else:
            rows.append((round(t,5), d, round(d * mm_per_px,5)))

    df = pd.DataFrame(
        rows, columns=["time_s", "distance_px", "elongation_mm"]
    )
    df.to_csv(output_full, index=False)

    # ======================================================
    # 2) Save relative CSV
    # ======================================================
    # Find first and last significant change in displacement
    first_change = None
    last_change = None
    prev = None

    for i, e in enumerate(df["elongation_mm"]):
        if pd.isna(e):
            continue
        if prev is None:
            prev = e
            continue
        if e != prev:
            if first_change is None:
                first_change = max(i - 1, 0)
            last_change = i  # update until last change
        prev = e

    # If there were not changes, take the whole range
    if first_change is None:
        first_change = 0
    if last_change is None:
        last_change = len(df) - 1

    df_rel = df.iloc[first_change:last_change + 1].copy()
    t0 = df_rel.iloc[0]["time_s"]
    df_rel["time_s"] -= t0

    df_rel.to_csv(output_relative, index=False)

    print("Body 3d displacement results (both the full csv and the filtered csv) saved in body3d_output")
