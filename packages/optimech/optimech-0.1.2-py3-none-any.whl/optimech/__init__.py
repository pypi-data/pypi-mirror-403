"""
Optimech: Python library for experimental mechanics

This library provides tools to analyze:
1) Tensile tests using optical extensometry
2) Displacement of 3d-printed bodies under load

High-level functions:
---------------------
- analyze_tensile(...)       : Analyze tensile test video/images
- plot_tensile_results(...)  : Plot elongation and strain over time
- animate_tensile_gauge(...) : Animate gauge tracking

- analyze_body3d(...)        : Analyze 3d-printed body displacement
- plot_body3d_displacement(...) : Plot displacement vs time
- make_body3d_gif(...)      : Animate tracked displacement points
"""

# ==========================================================
# Submodules
# ==========================================================
from . import tensile
from . import body3d

# ==========================================================
# High-level aliases from tensile
# ==========================================================
from .tensile import (
    analyze as analyze_tensile,
    plot_results as plot_tensile_results,
    animate_gauge as animate_tensile_gauge
)

# ==========================================================
# High-level aliases from body3d
# ==========================================================
from .body3d import (
    analyze as analyze_body3d,
    plot_displacement_vs_time as plot_body3d_displacement,
    make_tracking_gif as make_body3d_gif
)

# ==========================================================
# Expose submodules and high-level API
# ==========================================================
__all__ = [
    # Submodules
    "tensile",
    "body3d",

    # Tensile high-level
    "analyze_tensile",
    "plot_tensile_results",
    "animate_tensile_gauge",

    # Body3d high-level
    "analyze_body3d",
    "plot_body3d_displacement",
    "make_body3d_gif",
]

__version__ = "0.1.2"
