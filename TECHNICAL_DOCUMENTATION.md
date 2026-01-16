# Nebula Python Wrapper Technical Documentation

## Core Algorithms and Implementation Details

This document describes in detail the core algorithms and implementation details used in the Nebula Python Wrapper project, providing developers and researchers with a reference for in-depth understanding of the project's internal working mechanisms.

## 1. SEM Electron Beam Data Generation

### 1.1 Algorithm Principles

The `generate_sem_pri_data` function in `sem_pri.py` implements the generation of scanning electron microscope (SEM) electron beam data. This algorithm is based on the following physical and mathematical models:

#### Electron Beam Distribution Model

- **Spatial Distribution**: Uses Gaussian distribution to simulate spatial distribution of electron beam spot, where `sigma` parameter controls spot size
- **Energy Distribution**: All electrons have the same initial energy specified by `energy` parameter
- **Direction Distribution**: Electron initial direction specified by `dx`, `dy`, `dz` parameters, typically set to (0, 0, -1) indicating along negative z-axis

#### Electron Number Model

- **Deterministic Model**: Each pixel has a fixed number of electrons specified by `epx` parameter
- **Random Model**: Uses Poisson distribution to simulate electron number randomness with mean value `epx`, closer to physical characteristics of real electron beams

### 1.2 Data Structure

Electron data is stored using the following NumPy structure:

```python
electron_dtype = np.dtype([
    ('x',  '=f'), ('y',  '=f'), ('z',  '=f'),  # Position
    ('E',  '=f'),                              # Energy
    ('px', '=i'), ('py', '=i')                 # Pixel index
])
```

### 1.3 Optimization Strategies

To handle large amounts of electron data, the algorithm adopts the following optimization strategies:

1. **Batch Processing**: Processes large amounts of electrons in batches, maximum 10,000 electrons per batch, reducing memory usage
2. **Progress Reporting**: Displays progress every 10% of pixels processed, providing remaining time estimate
3. **Memory Estimation**: Estimates required memory and file size before starting processing to avoid memory overflow

## 2. Mesh Processing and Transformation

### 2.1 STL to TRI Conversion

`process_stl_to_tri.py` implements conversion from standard STL files to the TRI format used by the project:

1. **STL Parsing**: Reads binary or ASCII format STL files, extracting triangle facet data
2. **Coordinate Transformation**: Applies scaling and translation transformations to adjust model to appropriate size and position
3. **TRI Format Generation**: Generates TRI files containing material information and triangle vertex coordinates

### 2.2 Mesh Rotation Algorithm

`rotate_cylinder.py` and `generate_cylinder_mesh.py` implement mesh rotation algorithms:

```python
# Rotation matrix calculation
tilt_x_rad = math.radians(tilt_x)
cos_tx = math.cos(tilt_x_rad)
sin_tx = math.sin(tilt_x_rad)

# Apply rotation transformation
y_r = y * cos_tx - z * sin_tx
z_r = y * sin_tx + z * cos_tx
```

This rotation implements rotation transformation around the x-axis, used to simulate sample or detector tilt.

### 2.3 Voxel to Mesh Conversion

The `run_interface` function in `voxel_to_mesh.py` implements conversion from voxel data to triangle mesh:

1. **Voxel Data Loading**: Loads voxel data from NumPy arrays or other formats
2. **Surface Extraction**: Uses Marching Cubes or similar algorithm to extract voxel data surface
3. **Mesh Simplification**: Simplifies mesh as needed to reduce triangle count
4. **Mesh Smoothing**: Applies smoothing algorithms to improve mesh quality
5. **Coordinate Transformation**: Applies rotation, scaling and other transformations to adjust mesh position and orientation

```python
def run_interface(
                voxel_path,              # STL/voxel data path (commonly STL in this project)
                mesh_path,               # Output directory (generate .tri files)
                final_side=1000,         # Target size (side length); STL workflow uses max bbox edge as baseline
                scale=10,                # Vertex coordinate scaling factor (STL -> nm for calculation convenience)
                sample_tilt_x=0,         # Sample tilt angle around X axis
                sample_tilt_y=0,         # Sample tilt angle around Y axis
                sample_tilt_new_z=0,     # Rotation angle around sample normal direction after tilting (calculated by rotation_matrix)
                det_tilt_x=0,            # Detector tilt angle around X axis (for detector facets)
                pad_scale=1.0,           # Used in voxel workflow (ignored in STL workflow)
                length=64,               # Used in voxel workflow (ignored in STL workflow)
                reverse=False            # Used in voxel workflow (ignored in STL workflow)
                ):
```

Description: In STL workflow, reads triangle mesh (trimesh), scales by `scale` factor and centers by bbox; then applies tilt and rotation around normal matrix `R` (see `rotation_matrix.py`), then writes out TRI. Function returns: `v, faces, d_zmin, d_zmax, tri_file_path, R`, where `d_zmin/d_zmax` comes from detector triangle z range, used to determine electron beam z position when generating .pri.

Additional: TRI Generation and Material Encoding Conventions (excerpts)
- Sample triangle rows: `0 -123 x y z x1 y1 z1 x2 y2 z2`
- Detector triangle rows: `-125 -125 ...` (36-sided approximate circle, supports `det_tilt_x` rotation and z+=34 upward shift, finally uniformly converted to nanometers)
- Environment enclosures: `-122 -122` (walls), `-127 -127` (bottom)

Nebula Executable Call and Progress Monitoring (run_nebula.py summary)
- `nebula_gpu.run()` uses `subprocess.Popen(..., shell=True)` to execute complete command (including redirection), and monitors stderr:
    - Terminates process and prompts to optimize input when detecting `running: 0 | detected: 0`
    - After detecting `Progress 100.00%`, waits 20 seconds; if still not exited, actively terminates to avoid hanging, then continues to display results
- Result display uses `analysis.sem_analysis` to convert `.det` to image and save

## 3. Detector Simulation

### 3.1 Detector Geometry Model

Detector is represented using triangle mesh, its position and orientation can be adjusted through the following parameters:

- **Detector tilt angle**: Typically 76.8 degrees for electron beam imaging or 0 degrees, 55 degrees etc. for ion beam imaging
- **Detector position**: Position relative to sample, typically placed above sample

### 3.2 Electron-Detector Interaction

When simulated electrons intersect with detector, the following information is recorded:

- Electron energy
- Electron incident angle
- Intersection point position
- Corresponding original pixel coordinates

This information is used to generate final simulated images.

## 4. Graphical User Interface Implementation

### 4.1 Interface Architecture

`nebula_gui.py` uses PyQt6 to implement graphical user interface, adopting the following architecture:

1. **Main Window**: `NebulaGUI` class inherits from `QMainWindow`, serves as application main window
2. **Tab Interface**: Uses `QTabWidget` to create multiple functional tabs
3. **Parameter Configuration Area**: Uses various Qt widgets (such as `QLineEdit`, `QSpinBox` etc.) to collect user input
4. **Action Buttons**: Provides buttons for execute, cancel and other operations
5. **Output Display Area**: Uses `QTextEdit` or `QPlainTextEdit` to display operation results and logs

### 4.2 Multithreading Processing

To avoid interface freezing during time-consuming operations, GUI uses Qt's multithreading mechanism:

```python
class WorkerThread(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)
    
    def __init__(self, function, args):
        super().__init__()
        self.function = function
        self.args = args
        
    def run(self):
        result = self.function(*self.args)
        self.finished.emit(result)
```

### 4.3 Settings Persistence

Uses `QSettings` to save and load user settings, ensuring user configurations remain valid after application restart:

```python
settings = QSettings("NebulaGPU", "NebulaGUI")
settings.setValue("nebula_gpu_path", path)
```

## 5. Ion Beam and Electron Beam Imaging Modes

### 5.1 Ion Beam Imaging Mode

Ion beam imaging mode characteristics:

- Detector tilt angle typically 55 degrees or 52 degrees
- Ion beam emission direction perpendicular to detector plane
- Sample tilt angle typically same as detector tilt angle, making sample surface perpendicular to ion beam direction

Implementation in code:

```python
if electron_ion_um["ion_beam"] == beam_type:
    sample_tilt_x = 55    # Sample tilt angle
```

### 5.2 Electron Beam Imaging Mode

Electron beam imaging mode characteristics:

- Detector tilt angle is 76.8 degrees
- Electron beam incidence direction fixed along z-axis direction (tilt angle 0 degrees)
- Sample can be tilted arbitrarily, typically 0 degrees

Implementation in code:

```python
elif electron_ion_um["electron_beam"] == beam_type:
    sample_tilt_x = 0   # Sample tilt angle, can choose any angle
    det_tilt_x = 76.8  # Detector tilt angle
```

## 6. File Format Specifications

### 6.1 TRI File Format

TRI file is a text format, each line describes a triangle facet:

```
material1 material2 x y z x1 y1 z1 x2 y2 z2
```

Where:
- `material1`, `material2`: Material identifiers on both sides of triangle
- `x`, `y`, `z`: Coordinates of first vertex
- `x1`, `y1`, `z1`: Coordinates of second vertex
- `x2`, `y2`, `z2`: Coordinates of third vertex

### 6.2 PRI File Format

PRI file is a binary format storing electron beam data, each electron record contains:

- Position (x, y, z): Electron three-dimensional coordinates
- Direction (dx, dy, dz): Electron motion direction vector
- Energy (E): Electron energy, unit eV
- Pixel index (px, py): Corresponding pixel coordinates

### 6.3 DET File Format

DET file stores detector-captured electron data, contains:

- Electron energy
- Electron incident angle
- Intersection point position
- Corresponding original pixel coordinates

## 7. Performance Considerations

### 7.1 Memory Management

Memory management strategy when processing large datasets in project:

1. **Batch Processing**: Processes large amounts of data in batches to avoid loading all data at once
2. **Memory Pre-estimation**: Estimates required memory before starting processing, warns of possible memory shortage in advance
3. **Temporary Files**: Uses temporary files to store intermediate results for very large datasets

### 7.2 Computational Optimization

Strategies to improve computational efficiency:

1. **Vectorized Operations**: Uses NumPy vectorized operations instead of loops
2. **Parallel Computing**: Uses multithreading or multiprocessing where appropriate
3. **GPU Acceleration**: Uses PyTorch for GPU acceleration for CUDA-supported operations

## 8. Extension and Customization

### 8.1 Adding New Mesh Generators

To add new mesh generators, need to:

1. Create a new Python module implementing mesh generation algorithm
2. Add corresponding interface elements in `nebula_gui.py`
3. Integrate new functionality into existing workflow

### 8.2 Supporting New Material Properties

To support new material properties, need to:

1. Extend MAT file format, add new property fields
2. Modify related processing code to consider effects of new properties
3. Update GUI to allow users to set new properties

### 8.3 Custom Simulation Parameters

Users can customize simulation parameters through the following methods:

1. Set parameters through GUI interface
2. Directly modify configuration files
3. Pass custom parameters when calling related functions in code

## 9. Debugging and Troubleshooting

### 9.1 Common Issues

1. **Module Import Error**: Usually caused by package directory structure not matching package structure defined in `setup.py`
2. **File Path Error**: Ensure using absolute paths or correct relative paths
3. **Out of Memory**: May encounter memory shortage when processing large datasets, try reducing dataset size or using batch processing

### 9.2 Debugging Techniques

1. **Logging**: Use Python's `logging` module to record key operations and intermediate results
2. **Breakpoint Debugging**: Set breakpoints in IDE to execute code step by step
3. **Visualize Intermediate Results**: Save intermediate results as images or other visual forms to help understand algorithm behavior

## 10. Future Development Plans

### 10.1 Short-term Plans

1. **Performance Optimization**: Improve efficiency of large dataset processing
2. **User Interface Improvements**: Add more visualization options and real-time preview functionality
3. **Documentation Completion**: Add detailed API documentation for each module

### 10.2 Long-term Plans

1. **Support More Materials and Simulation Parameters**: Extend system to support broader range of materials and simulation scenarios
2. **Integrate Machine Learning Models**: Use machine learning to accelerate simulation process or improve result quality
3. **Distributed Computing Support**: Support running large-scale simulations on clusters

## 11. Images to Video Module (images_to_video_gui.py)

This module provides a PyQt6-based desktop GUI for selecting multiple images and generating videos. Core design points are as follows:

### 11.1 Architecture and Threading Model

- UI Layer: `ImageToVideoApp(QMainWindow)`
    - Image selection and path list display (supports multiple additions, across folders)
    - Sorting (by filename / modification time)
    - Output parameter settings: frame rate, resolution (preset/custom), aspect ratio strategy (maintain/stretch), quality (high/standard/compressed)
    - Progress bar and message popups
- Worker Thread: `VideoGeneratorThread(QThread)`
    - Input: `image_paths: List[str]`, `output_path: str`, `fps: int`, `size: Optional[Tuple[int,int]]`, `keep_aspect: bool`, `quality: int`
    - Signals: `progress_updated(int)`, `finished(str)`, `error_occurred(str)`
    - Function: Serially loads images, adapts dimensions, writes video frames in child thread to avoid UI blocking

Data flow (brief "contract"):
- Input: N image paths, target video parameters (fps, size, strategy/quality)
- Process: Read image by image → dimension adaptation (maintain/stretch + interpolation) → write frame
- Output: Video file (mp4/avi), progress 0→100, errors reported via signals

### 11.2 Dimension and Interpolation Strategy

- If size not specified, automatically uses first image size
- `keep_aspect=True`: Scales proportionally then centers on canvas, fills blank space with black; `False`: directly scales to target size
- Interpolation method selected based on quality level:
    - High quality: `cv2.INTER_CUBIC`
    - Standard: `cv2.INTER_LINEAR`
    - Compressed: `cv2.INTER_AREA`
- For compatibility with some encoders, forces target width/height adjustment to even numbers

### 11.3 Encoder and Fallback Strategy

Attempt order:
1. HEVC/H.265 (fourcc: `hev1`)
2. H.264 (fourcc: `avc1`)
3. MPEG-4 (fourcc: `mp4v`)

If current OpenCV build does not support first two, automatically fallback to `mp4v` to ensure successful generation. Container recommendation prioritizes `.mp4`, better compatibility; if fails can try `.avi`.

### 11.4 Error Handling and Robustness

- I/O errors and read failures: For each image `cv2.imread` failure immediately throws error and transmitted through `error_occurred` signal
- Write failure: After multiple fallbacks `cv2.VideoWriter.isOpened()` still fails then reports error
- Cancel and exit: If thread still running when UI closes, calls `stop()` to set `_is_running=False` and waits for thread to finish
- Large batch images: >100 images pops up confirmation to avoid misoperation

### 11.5 Performance and Memory

- Single-threaded serial processing, suitable for I/O intensive and easy to ensure order
- Memory usage mainly from current frame, suitable for medium resolution and medium quantity images
- For very high resolution or very long sequences recommend: reducing resolution/quality; or expanding to streaming/chunked reading in future

### 11.6 Compatibility Notes

- Available encoders in OpenCV on different platforms vary; on Linux commonly `mp4v` available, HEVC/H.264 depends on build
- When generation fails prioritize checking: output path permissions, extension (.mp4/.avi), whether resolution too large

## 12. Engineering Configuration and Development Workflow

To facilitate unified style and improve development efficiency, project provides the following configurations and tools:

- Code style configuration (`pyproject.toml`)
    - black: `line-length=100`
    - isort: `profile=black`
    - ruff: Enables common rules (E/F/I), ignores `source/__pycache__`
- Development dependencies (`requirements-dev.txt`): `ruff`, `black`, `isort`
- Makefile common targets:
    - `make install`: Install runtime dependencies
    - `make install-dev`: Install development dependencies
    - `make format`: black + isort formatting
    - `make lint`: ruff checking
    - `make gui`: Run Images to Video GUI
    - `make sem`: Run `sem-analysis.py`
    - `make sim`: Run `auto_run_simulation.py`
- VS Code (optional, repository defaults to ignoring `.vscode/`):
    - `tasks.json`: One-click run GUI/scripts, install dependencies, format, lint
    - `extensions.json`: Recommended extensions (Python, Pylance, Ruff, Black, Jupyter)

## 13. Compatibility and Deployment Recommendations

- Python version: Recommended 3.9+ (project contains `__pycache__` py3.13 bytecode, actual runtime version needs to match local environment)
- OpenCV encoders:
    - If need HEVC/H.264, use build containing corresponding codec support; otherwise use `.mp4` + `mp4v` to ensure success
    - Resolution needs to be even numbers, very large resolution may fail on low-spec machines
- GUI runtime environment: Needs graphical desktop and `PyQt6`; server environment recommend expanding CLI headless mode in future

## 14. Testing and Validation Recommendations

- Unit tests (recommend adding):
    - Parameter parsing and dimension calculation: `_get_video_size`, even width/height correction
    - Sorting functionality: Whether sorting by name/date is stable
- Integration tests:
    - Use 5~10 small images (like 640x480) to generate short video (2~3 seconds) to verify encoder fallback logic
    - Generate `.mp4` and `.avi`, ensure at least one container succeeds
- Stress testing (manual):
    - 1000+ images, 1080p/4K, observe memory and time, guide user parameter recommendations
