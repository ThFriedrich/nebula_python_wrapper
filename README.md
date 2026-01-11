# Nebula Python Wrapper

A collection of Python tools and scripts for Nebula simulation, including utilities for running/analyzing simulation results, as well as a desktop GUI tool for converting images to video, making it easy to combine multiple images into MP4/AVI videos.

- Language: Python
- Platform: Linux (primary support), other platforms may work (depends on dependency availability)

---

## Feature Overview
- Run Nebula simulations and process output data
- Auxiliary scripts for generating/managing meshes and simulation parameters
- SEM analysis scripts and visualization
- New: Images to Video GUI (select multiple images at once, set frame rate/resolution/quality and export)

---

## Installation and Environment

Recommended to use in a virtual environment or Conda environment:

```bash
# Clone repository
git clone <your-repo-url-or-ssh>
cd nebula_python_wrapper

# Install dependencies
pip install -r requirements.txt

# Optional: Development mode installation (provides entry scripts, see setup.py)
pip install -e .
```

Main dependencies:
- numpy
- matplotlib
- PyQt6 (graphical interface)
- opencv-python (video encoding)

> Note: OpenCV binary packages on different platforms have different video encoders. This project will automatically fallback between HEVC/H.265, H.264, and mp4v to ensure successful generation.

---

## Quick Start

### 1) Images to Video GUI (Images → Video)

Launch GUI:

```bash
python source/images_to_video_gui.py
```

Features and operations:
- Select images:
  - "Select Images" replaces current selection
  - "Add More Images" appends to existing selection
  - "Add Folder" batch imports from entire directory
- Sorting: Sort by "Name/Date"
- Output: Select output file (recommended .mp4)
- Parameters: Set frame rate (FPS), resolution (preset or custom), aspect ratio strategy (maintain/stretch), quality (high/standard/compressed)
- Progress: Bottom progress bar shows real-time progress

Details:
- Supported formats: .png, .jpg, .jpeg, .bmp, .tif, .tiff
- Resolution:
  - Provides 4K/2K/1080p/720p/480p presets or custom width/height
  - For encoder compatibility, program automatically corrects odd width/height to even numbers
- Aspect ratio:
  - Maintain: Scale proportionally and fill empty space with black borders
  - Stretch: Directly scale to target size (may distort)
- Quality options:
  - High quality: Clear but larger files (Cubic interpolation)
  - Standard: Balance quality and speed (Linear interpolation)
  - Compressed: Smaller size, suitable for preview (Area interpolation)
- Encoder fallback:
  1) HEVC/H.265 (hev1) → 2) H.264 (avc1) → 3) mp4v
  If the first two are unavailable, automatically fallback to mp4v (best compatibility)

Common issues:
- Cannot create video file:
  - Try .mp4 or .avi extension
  - Confirm output directory is writable
  - Reduce resolution or select "Standard/Compressed"
- HEVC/H.264 unavailable:
  - OpenCV without these encoders is common; program will fallback to mp4v
- GUI startup fails:
  - Confirm PyQt6 is installed: `pip install PyQt6`
  - Reinstall dependencies: `pip install -r requirements.txt`

### 2) SEM Analysis and Simulation Scripts

Example: Run SEM analysis script (adjust paths as needed):

```bash
python source/sem-analysis.py
```

Automatic simulation script:

```bash
python source/auto_run_simulation.py
```

Script workflow overview (`source/auto_run_simulation.py`):
- Iterate through .stl files in `stl_dir`
- Generate .tri / .pri files
- Call Nebula executable to run simulation
- Save images (.png) and camera parameters (JSON)

Key parameters (at top of script):
- `mat_paths_list`: List of material `.mat` file paths
- `nebula_gpu_path`: Nebula executable path (ensure it exists and is executable)
- `stl_dir`: Input STL directory
- `output_path`: Output `.det` file path
- Others: `rotate_angle_*`, `roi_array`, `pixel_size`, `energy`, `epx`, etc.

> Tip: Path formats differ across systems, modify as needed; ensure paths exist and have proper permissions.

---

## Project Structure

```
nebula_python_wrapper/
├── CHANGELOG.md
├── PROJECT_DOCUMENTATION.md
├── README.md
├── requirements.txt
├── setup.py
├── TECHNICAL_DOCUMENTATION.md
├── troubleshooting.md
├── USER_GUIDE.md
├── docs/
│   └── nebula_gpu_python_wrapper_doc.md
└── source/
    ├── __init__.py
    ├── analysis.py
    ├── auto_run_simulation.py
    ├── generate_circular_mesh.py
    ├── generate_cylinder_mesh.py
    ├── generate_tri_pri.py
    ├── images_to_video_gui.py      # Images to Video GUI
    ├── nebula_gpu                  # Nebula executable (Linux example)
    ├── nebula_gui.py
    ├── parameters.py
    ├── process_stl_to_tri.py
    ├── read_stl_to_txt.py
    ├── rotate_cylinder.py
    ├── rotation_matrix.py
    ├── run_nebula.py
    ├── save_parameters.py
    ├── sem-analysis.py
    ├── sem_pri.py
    ├── tri_view_gui.py
    └── voxel_to_mesh.py
```

---

## Troubleshooting

- Video quality or size not ideal:
  - Reduce resolution/frame rate, select "Compressed" quality; unified image sizes can reduce interpolation processing
- Inconsistent image sizes:
  - Automatically adapted by strategy; "Maintain" will produce black borders, "Stretch" may distort
- "Cannot read image":
  - Confirm path exists and file is not corrupted; try removing special characters from path
- Simulation fails with executable not found:
  - Check if `nebula_gpu_path` is correct, on Linux needs execute permission (`chmod +x`)

---

## Contributing
1. Fork this repository
2. Create a branch for features or fixes
3. Submit PR and explain motivation and details of changes

## License
MIT
