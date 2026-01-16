# Nebula Python Wrapper User Guide

## Introduction

Nebula Python Wrapper is a collection of Python scripts and tools for running and analyzing Nebula simulation results. This document will help you install, configure, and use these scripts to complete scanning electron microscope (SEM) and ion beam imaging related simulations, data conversion, and visualization, while also including a desktop GUI tool for "Images to Video".

Last updated: 2025-09-30

## Table of Contents

1. [Installation Guide](#1-installation-guide)
2. [Quick Start](#2-quick-start)
3. [Graphical Interface: Images to Video](#3-graphical-interface-images-to-video)
4. [Command/Script Entry Points](#4-commandscript-entry-points)
5. [Programming Interface Usage (Examples)](#5-programming-interface-usage-examples)
6. [Common Workflows](#6-common-workflows)
7. [File Format Descriptions](#7-file-format-descriptions)
8. [Frequently Asked Questions](#8-frequently-asked-questions)
9. [Troubleshooting](#9-troubleshooting)
10. [Advanced Features](#10-advanced-features)
11. [Additional Resources](#11-additional-resources)

## 1. Installation Guide

### System Requirements

- Python 3.9+ (recommended)
- Linux preferred; other platforms can be attempted based on dependency availability
- GPU optional (for acceleration), CPU also works
- Recommended 16GB+ RAM, disk space ≥ 10GB

### Installation Steps

1. Clone repository

   ```bash
   git clone https://github.com/chenguisen/nebula_python_wrapper.git
   cd nebula_python_wrapper
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Optional: Development mode installation (convenient for subsequent development)

   ```bash
   pip install -e .
   ```

4. Optional: Verify environment

   ```bash
   python -V
   pip list | grep opencv
   ```

Tip: This project has added an "Images to Video" tool, which depends on opencv-python and PyQt6, already included in requirements.txt.

## 2. Quick Start

### Basic Concepts

Main data types involved in the project:

- STL: Standard format for 3D models
- TRI: Triangle mesh with material tags (one of Nebula's inputs)
- PRI: Electron/ion beam pixel scan data (one of Nebula's inputs)
- DET: Detector output data (Nebula's output)

### Quick Example

Method A: One-click SEM simulation (recommended)

```bash
python source/auto_run_simulation.py
```

Before running, you can modify the following parameters at the top of the script:
- `mat_paths_list`: List of material .mat files
- `nebula_gpu_path`: Nebula executable path (ensure it exists and is executable)
- `stl_dir`: Input STL directory
- Others: `pixel_size`, `energy`, `epx`, tilt angles and rotation lists, etc.

Method B: Images to Video GUI (combine multiple images into video)

```bash
python source/images_to_video_gui.py
```

This GUI supports multi-select images, sorting, setting frame rate/resolution/quality, and automatically adapts encoders (HEVC→H.264→mp4v fallback).

## 3. Graphical Interface: Images to Video

This repository provides a PyQt6 desktop application to quickly combine multiple images into MP4/AVI videos.

### Startup

```bash
python source/images_to_video_gui.py
```

### Key Features

- Image import: Select images/add more/import from folder; supports .png/.jpg/.jpeg/.bmp/.tif/.tiff
- Sorting: By name or date
- Output: Select target video file (recommended .mp4)
- Parameters: FPS, resolution (preset or custom), aspect ratio (maintain/stretch), quality (high/standard/compressed)
- Details: Automatically corrects odd width/height to even numbers; encoder auto-fallback ensures successful generation

Tip: For encoder compatibility, black borders/stretch descriptions, and common issues, see the README's "Images to Video GUI" section.

## 4. Command/Script Entry Points

In addition to the GUI, this project provides several directly runnable scripts suitable for batch processing and automation:

### Common Scripts

1) Run SEM analysis (adjust internal script paths as needed)

```bash
python source/sem-analysis.py
```

2) Run complete simulation (automatically generate .tri/.pri and call Nebula)

```bash
python source/auto_run_simulation.py
```

3) Use Makefile shortcut commands (optional)

```bash
make install       # Install dependencies
make gui           # Launch Images to Video GUI
make sem           # Run sem-analysis.py
make sim           # Run auto_run_simulation.py
make format        # Code formatting (black/isort)
make lint          # Code checking (ruff)
```

Note: Some shell scripts and commands mentioned in older documentation (such as `run_tri_pri_generator.sh`, `nebula-sem-analysis` console command) are not provided in the current repository, please use the above scripts.

## 5. Programming Interface Usage (Examples)

Nebula Python Wrapper provides a Python programming interface allowing you to use its functionality in your own scripts.

### Import Modules

```python
# TRI/PRI generation and Nebula execution (brief example)
from source.parameters import tri_parameters, pri_parameters
from source.run_nebula import nebula_gpu
import pathlib

stl_path = pathlib.Path('/path/to/model.stl')
mesh_path = stl_path.parent / 'mesh_out'

# 1) Generate TRI
TRI = tri_parameters(
   stl_path=stl_path,
   mesh_path=mesh_path,
   beam_type='electron',
   sample_tilt_x=0,
   sample_tilt_y=0,
   sample_tilt_new_z=0,
   det_tilt_x=76.8,
)
v, faces, d_zmin, d_zmax, tri_file_path, R = TRI.run()

# 2) Generate PRI (example)
PRI = pri_parameters(
   pri_dir=str(stl_path.parent),
   pixel_size=2,
   energy=500,
   epx=500,
   sigma=1.0,
   poisson=True,
   roi_x_min=-256, roi_x_max=255,
   roi_y_min=-256, roi_y_max=255,
   d_zmin=d_zmin, d_zmax=d_zmax,
)
pri_file_path = PRI.run()

# 3) Call Nebula to run
nebula_exe = pathlib.Path('source/nebula_gpu')  # Modify to your executable path
det_out = stl_path.parent / 'output.det'
cmd = f'"{nebula_exe}" "{tri_file_path}" "{pri_file_path}" /path/to/materials/silicon.mat > "{det_out}"'

NEBULA = nebula_gpu(command=cmd, sem_simu_result=str(det_out), image_path=tri_file_path.with_suffix('.png'))
NEBULA.run()
```

### Generate SEM Electron Beam Data

```python
import numpy as np
from source.sem_pri import generate_sem_pri_data

# Set parameters
z = 150                            # Starting z position (nm)
xpx = np.linspace(-128, 128, 512)  # x pixel range
ypx = np.linspace(-128, 128, 512)  # y pixel range
energy = 500                       # Electron beam energy (eV)
epx = 1000                         # Number of electrons per pixel

# Generate data
generate_sem_pri_data(
    z=z,
    xpx=xpx,
    ypx=ypx,
    energy=energy,
    epx=epx,
    sigma=1.0,
    poisson=True,
    file_path='data/sem.pri'
)
```

### Process STL Files

```python
from source.process_stl_to_tri import process_stl_to_tri

# Convert STL to TRI
process_stl_to_tri(
    input_file='data/model.stl',
    output_file='data/model.tri',
    scale=1.0,
    translate=[0, 0, 0]
)
```

### Voxel to Mesh Conversion

```python
from source.voxel_to_mesh import run_interface

# Convert voxel data to mesh
v, faces, d_zmin, d_zmax = run_interface(
    voxel_path='data/voxel_data.npy',
    mesh_path='data/',
    final_side=1000,
    sample_tilt_x=0,
    det_tilt_x=76.8
)
```

## 6. Common Workflows

### Electron Beam Imaging Workflow

1. **Prepare 3D model** (STL format)
2. **Convert to TRI format**
3. **Set sample tilt angle** (typically 0 degrees)
4. **Set detector tilt angle** (76.8 degrees)
5. **Generate PRI file**
6. **Run simulation**
7. **Analyze results**

### Ion Beam Imaging Workflow

1. **Prepare 3D model** (STL format)
2. **Convert to TRI format**
3. **Set sample tilt angle** (typically 55 degrees)
4. **Set detector tilt angle** (0 degrees)
5. **Generate PRI file**
6. **Run simulation**
7. **Analyze results**

### Parameter Optimization Workflow

1. **Set baseline parameters**
2. **Run initial simulation**
3. **Analyze results**
4. **Adjust parameters**
5. **Re-run simulation**
6. **Compare results**
7. **Repeat steps 4-6 until satisfactory results obtained**

## 7. File Format Descriptions

### STL File

STL (STereoLithography) is a standard file format representing 3D models, which can be binary or ASCII format.

### TRI File

TRI file is a text format, with each line describing a triangle facet:

```
material1 material2 x y z x1 y1 z1 x2 y2 z2
```

Where:
- `material1`, `material2`: Material identifiers on both sides of the triangle
- `x`, `y`, `z`: Coordinates of the first vertex
- `x1`, `y1`, `z1`: Coordinates of the second vertex
- `x2`, `y2`, `z2`: Coordinates of the third vertex

### PRI File

PRI file is a binary format storing electron beam data, each electron record contains:

- Position (x, y, z)
- Direction (dx, dy, dz)
- Energy (E)
- Pixel index (px, py)

### DET File

DET file stores detector-captured electron data, including electron energy, incident angle, intersection point position, and corresponding original pixel coordinates.

## 8. Frequently Asked Questions

### Q: How to choose appropriate electron beam energy?

A: Electron beam energy typically ranges from 100eV to 30keV. Lower energy is suitable for surface analysis, higher energy for deep layer analysis. For most applications, 500eV is a good starting point.

### Q: How to improve simulation accuracy?

A: Methods to improve simulation accuracy:
- Increase number of electrons per pixel (`epx` parameter)
- Reduce beam spot size (`sigma` parameter)
- Increase pixel resolution (increase length of `xpx` and `ypx` arrays)

### Q: How to handle large models?

A: Recommendations for handling large models:
- Use mesh simplification techniques to reduce triangle count
- Increase system memory
- Use batch processing methods
- Consider using GPU acceleration

### Q: What's the difference between electron beam and ion beam imaging?

A: Main differences:
- Electron beam: Detector tilt angle is 76.8 degrees, electron beam along z-axis direction
- Ion beam: Detector tilt angle is 0 degrees or 55 degrees, ion beam perpendicular to detector plane

## 9. Troubleshooting

### Module Import Error

**Problem**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check if package directory structure matches package structure defined in `setup.py`
3. Try reinstalling package: `pip install -e .`

### Out of Memory

**Problem**: `MemoryError` or program crash

**Solution**:
1. Reduce dataset size or resolution
2. Use batch processing methods
3. Increase system memory
4. Close other memory-intensive applications

### File Path Error

**Problem**: `FileNotFoundError: No such file or directory`

**Solution**:
1. Use absolute paths instead of relative paths
2. Ensure filename and path have no special characters
3. Check file permissions

### GPU Related Errors

**Problem**: CUDA related errors

**Solution**:
1. Ensure compatible CUDA drivers are installed
2. Check if GPU memory is sufficient
3. Try reducing batch size
4. If problem persists, switch to CPU mode

## 10. Advanced Features

### Custom Material Properties

You can define new material properties by creating custom MAT files:

1. Create a text file with one property and its value per line
2. Save as `.mat` file
3. Use the file in simulation

### Batch Simulation

For cases requiring multiple simulations, you can create batch processing scripts:

```bash
#!/bin/bash

# Batch simulation example
for energy in 100 200 500 1000; do
    echo "Running simulation with energy $energy eV"
    python source/sem_pri.py --energy $energy --output data/sem_${energy}eV.pri
    ./run_tri_pri_generator.sh data/sem_${energy}eV.pri
done
```

### Result Visualization

Use Matplotlib or other visualization tools to analyze results:

```python
import matplotlib.pyplot as plt
import numpy as np

# Load result data
data = np.load('data/simulation_results.npy')

# Create heatmap
plt.figure(figsize=(10, 8))
plt.imshow(data, cmap='viridis')
plt.colorbar(label='Electron Count')
plt.title('SEM Simulation Results')
plt.xlabel('X Pixel')
plt.ylabel('Y Pixel')
plt.savefig('data/simulation_results.png', dpi=300)
plt.show()
```

### Parameter Scanning

By systematically varying parameters and comparing results, you can find optimal parameter combinations:

```python
import numpy as np
from source.sem_pri import generate_sem_pri_data

# Parameter scanning example
energies = [100, 200, 500, 1000]
sigmas = [0.5, 1.0, 2.0]

for energy in energies:
    for sigma in sigmas:
        print(f"Testing energy={energy}eV, sigma={sigma}nm")
        generate_sem_pri_data(
            z=150,
            xpx=np.linspace(-128, 128, 256),  # Reduce resolution to speed up scanning
            ypx=np.linspace(-128, 128, 256),
            energy=energy,
            epx=500,
            sigma=sigma,
            file_path=f'data/scan_e{energy}_s{sigma}.pri'
        )
        # Run simulation and analyze results
        # ...
```

## 11. Additional Resources

- Quick Start (one-page cheat sheet): docs/QuickStart.md
- Project structure and workflow: PROJECT_DOCUMENTATION.md (contains Mermaid flowcharts)
- Design details and technical notes: TECHNICAL_DOCUMENTATION.md

## Conclusion

This user guide covers basic usage and advanced features of Nebula Python Wrapper. As you become familiar with the tools, you will be able to perform more complex simulations and analyses. If you have any questions or suggestions, please refer to the project documentation or contact the development team.

Happy using!
