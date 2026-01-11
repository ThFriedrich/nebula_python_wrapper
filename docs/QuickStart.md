# Quick Start

This page serves as a quick reference card to help you quickly run through the end-to-end STL→TRI→PRI→Nebula→DET→PNG workflow, listing key parameters and common issues.

## I. End-to-End Workflow (All-in-One)

1) STL → TRI (including tilt and rotation around normal)
- Entry point: `source/parameters.py` → `tri_parameters.run()` → `voxel_to_mesh.run_interface()`
- Output: `.tri`

2) ROI/energy etc. → PRI (electron beam input)
- Entry point: `source/parameters.py` → `pri_parameters.run()` → `sem_pri.generate_sem_pri_data()`
- Output: `.pri`

3) TRI + PRI + MAT → DET (call Nebula executable)
- Entry point: `source/run_nebula.py` → `nebula_gpu.run()`
- Output: `.det`

4) DET → PNG (visualization)
- Entry point: `source/analysis.py` → `sem_analysis()`
- Output: `.png`

Reusable scripts:
- Automatic batch processing: `python source/auto_run_simulation.py`
- Images to Video GUI: `python source/images_to_video_gui.py`

---

## II. Key Parameters Overview

- STL/Geometry
  - `sample_tilt_x / sample_tilt_y`: Sample tilt around X/Y axis
  - `sample_tilt_new_z`: Rotation angle around sample normal direction after tilting
  - `det_tilt_x`: Detector tilt angle around X axis
  - Encoding (TRI): Sample `0 -123`, Detector `-125 -125`, Environment `-122/-127`

- PRI/Electron beam
  - `pixel_size`: Pixel size (nm)
  - `energy`: Energy (eV/keV depending on implementation)
  - `epx`: Electrons per pixel (Poisson can be enabled)
  - `roi_x_min/x_max/y_min/y_max`: ROI region (pixel range)
  - `d_zmin / d_zmax`: Detector z range from TRI, used for beam z position calculation

- Executable/Materials
  - `nebula_gpu_path`: Nebula executable path (Linux example: `source/nebula_gpu`)
  - `mat_paths_list`: List of material `.mat` files (concatenated with spaces)
  - Command template: `"nebula_gpu" "tri" "pri" material1.mat material2.mat > output.det`

- Images to Video GUI (images_to_video_gui.py)
  - Support multiple image selection/append, sort by name/date
  - Frame rate, resolution (including custom), aspect ratio (maintain/stretch), quality (high/standard/compressed)
  - Encoder fallback: HEVC(hev1) → H.264(avc1) → mp4v; automatically corrects to even width/height

---

## III. Common Questions (FAQ)

- Video generation fails or file unusable
  - Try .mp4 or .avi; confirm output directory is writable
  - OpenCV may not include HEVC/H.264, program will fallback to mp4v

- Nebula executable path or material file does not exist
  - Check `nebula_gpu_path`, `.mat` paths; on Linux need `chmod +x`

- `running: 0 | detected: 0`
  - Geometry/PRI/material settings may have issues; script will terminate and prompt to optimize input

- Very high resolution or very long sequence video export takes too long
  - Reduce resolution/frame rate or select "standard/compressed"; prioritize mp4v for better compatibility

---

## IV. Recommended Development Workflow

- Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # optional
```

- Unified style and checks
```bash
make format
make lint
```

- Quick run
```bash
make gui       # Images to Video GUI
make sem       # SEM analysis script
make sim       # Automatic simulation script
```
