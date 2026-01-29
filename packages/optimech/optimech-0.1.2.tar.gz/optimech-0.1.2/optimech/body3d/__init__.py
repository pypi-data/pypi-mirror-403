"""
optimech.body3d

Module for displacement analysis of 3d-printed bodies under load
using video/image sequences.

Main features:
- Video frame extraction
- Contour-based displacement tracking
- Conversion from pixels to physical units
- CSV export and visualization utilities
"""

# ==========================================================
# 1) High-level functions
# ==========================================================
from .analysis import analyze
from .visualization import (
    plot_displacement_vs_time,
    make_tracking_gif,
)

# ==========================================================
# 2) Optional: internal modules for advanced users
# ==========================================================
from .video import extract_frames
from .tracking import track_displacement_px
from .vision import detect_contours, compute_reference_point

# ==========================================================
# 3) Expose public API
# ==========================================================
__all__ = [
    # Main entry point
    "analyze",

    # Visualization
    "plot_displacement_vs_time",
    "make_tracking_gif",

    # Advanced / low-level
    "extract_frames",
    "track_displacement_px",
    "detect_contours",
    "compute_reference_point",
]
