# optimech

**optimech** is a Python library for **optical-mechanical analysis of experimental tests using video data**.  
It is designed to process videos recorded during mechanical testing and extract **displacement and strain information** using computer vision techniques.

The library currently supports two analysis modules:

- **Tensile Test Program** (optical extensometry)
- **3D-Printed Body Program** (displacement measurement at contact or sensitive points)

The project is developed as part of the *Programming II* course and is distributed as a reusable Python package.

---

## Features

### Tensile Test Program (`optimech.tensile`)

- Video input support (smartphone or camera recordings)
- Automatic frame extraction
- Detection and cropping of the extensometer region
- Optical tracking of extensometer gauge lines
- Frame-by-frame displacement measurement
- Strain computation from gauge length
- Time-based analysis (fps-based)
- CSV export of displacement and strain data
- Static and interactive visualizations (Matplotlib / Plotly)

---

### 3D-Printed Body Program (`optimech.body3d`)

- Video input support for relaxed and loaded states
- Frame extraction from recorded tests
- Detection of contact or user-defined sensitive points
- Optical tracking of displacement at the contact point
- Measurement of deformation under actuator pressure
- Relative displacement computation between states
- CSV export of displacement results
- Visualization of tracked points and displacement evolution

---

## Installation

Install the library directly from PyPI:

```bash
pip install optimech
```

---

## Requirements

- Python ≥ 3.9
- NumPy
- OpenCV
- Matplotlib
- Plotly
- Pandas
- Imageio

All dependencies are installed automatically with pip.

---

## Basic Usage

### Tensile test analysis

```python
import optimech

results = optimech.analyze_tensile(gauge_length_mm=35, image_dir="pics", output_csv="tensile_results")
optimech.plot_tensile_results(results["time_s"], results["elongation_mm"], results["strain"], "tensile_plots")
optimech.animate_tensile_gauge(results["images_rgb"], results["top_lines"], results["bottom_lines"])
```

Main function (high-level API) processes the video and computes the displacement and strain from the extensometer using optical tracking techniques, for a specimen of 35mm gauge length and photos of the tensile test in the pics folder.

The other two are optional visualization  functions.

### 3D-printed body analysis

```python
import optimech

results3d = optimech.analyze_body3d(video_path="body3d.mov", specimen_height_mm=40)
optimech.plot_body3d_displacement(results3d["csv_relative"], "body3d_plots")
optimech.make_body3d_gif(results3d["frames_dir"], results3d["csv_full"], results3d["reference_point"], "body3d_plots")
```

Main function (high-level API) processes the video and computes the displacement of the contact point of the body and the actuator that applies that movement using optical tracking techniques, for a specimen of 40mm height and a video of the test in .mov format.

The other two are optional visualization  functions.

---

## Project structure

```text
optimech/
│
├── tensile/
│   ├── __init__.py
│   ├── analysis.py
│   ├── io.py
│   ├── tracking.py
│   ├── video.py
│   ├── vision.py
│   └── visualization.py
│
├── body3d/
│   ├── __init__.py
│   ├── analysis.py
│   ├── io.py
│   ├── tracking.py
│   ├── video.py
│   ├── vision.py
│   └── visualization.py
│
└── __init__.py
```

---

## API Design

The library exposes a simple and clear public API, as required by the project specification.

Internal processing steps such as video handling, vision algorithms, tracking and analysis are modularized internally and hidden from the user.

---

## Authors

- Amaia Marín
- Jone Morrás
- Nahia Uriarte
- Nora Vega

---

## License

This project is licensed under the MIT License.
See the LICENSE file for more details.
