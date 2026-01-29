import pandas as pd
import os


def save_tensile_csv(
    time_s,
    distance_px,
    elongation_mm,
    strain,
    output_csv: str,
    workdir: str,
):
    """
    Save tensile test results to a CSV file.

    Parameters
    ----------
    time_s : array-like
        Time values [s].
    distance_px : array-like
        Distance between extensometer lines [pixels].
    elongation_mm : array-like
        Elongation [mm].
    strain : array-like
        Engineering strain [-].
    output_csv : str
        Output CSV file path.
    workdir : str
        Directory where to save the CSV.
    """

    os.makedirs(workdir, exist_ok=True)
    filename = os.path.join(workdir, output_csv)

    df = pd.DataFrame({
        "time_s": time_s,
        "distance_px": distance_px,
        "elongation_mm": elongation_mm,
        "strain": strain,
    })

    df.to_csv(filename, index=False)

    print("Tensile test optical extensometry results saved in tensile_output/tensile_results")
