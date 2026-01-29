"""
Tensile test optical extensometry package

This package provides tools to:
- Extract frames from videos
- Crop extensometer region
- Track top/bottom gauge lines
- Compute elongation and strain
- Save results to CSV
- Visualize results and animate the gauge

Modules
-------
- analysis    : High-level pipeline to analyze a video or images
- tracking    : Track gauge distance in pixels
- vision      : Image processing utilities (line detection + crop)
- video       : Video frame extraction
- io          : CSV saving
- visualization : Plotting and animation
"""

# ==========================================================
# 1) High-level functions
# ==========================================================
from .analysis import analyze
from .visualization import plot_results, animate_gauge

# ==========================================================
# 2) Optional: internal modules for advanced users
# ==========================================================
from .tracking import track_gauge_distance_px
from .vision import crop_images, detect_extensometer_lines, find_black_line_rows, extract_top_bottom_lines
from .video import extract_frames
from .io import save_tensile_csv

# ==========================================================
# 3) Expose public API
# ==========================================================
__all__ = [
    "analyze",
    "plot_results",
    "animate_gauge",
    "track_gauge_distance_px",
    "crop_images",
    "detect_extensometer_lines",
    "find_black_line_rows",
    "extract_top_bottom_lines",
    "extract_frames",
    "save_tensile_csv",
]
