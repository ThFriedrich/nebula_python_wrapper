# Nebula GPU Python Wrapper Documentation

## Overview

This document describes how to wrap `nebula_gpu` (a program written in C++ and CUDA) as a Python module for calling from Python.

## Wrapping Steps

1. **Create Python Module**:
   - Wrote a Python script `nebula_wrapper.py` that wraps calls to `nebula_gpu`.
   - Script located at `/home/chenguisen/AISI/nebula/nebula/nebula_wrapper.py`.

2. **Functionality Implementation**:
   - Wrapped command-line arguments `sem.tri`, `sem.pri`, `silicon.mat`, `pmma.mat` as inputs to Python functions.
   - Supports redirecting output to a file or returning directly to Python.

3. **File Validation**:
   - Checks if input files exist before calling `nebula_gpu`.

## Usage

### Install Dependencies
Ensure Python 3 and the `subprocess` module (included in Python standard library) are installed on the system.

### Call Examples

1. **Save output to file**:
   ```python
   from nebula_wrapper import run_nebula_gpu

   run_nebula_gpu(
       "sem.tri",
       "sem.pri",
       "silicon.mat",
       "pmma.mat",
       "output.det"
   )
   ```

2. **Get output content directly**:
   ```python
   from nebula_wrapper import run_nebula_gpu

   output = run_nebula_gpu(
       "sem.tri",
       "sem.pri",
       "silicon.mat",
       "pmma.mat"
   )
   print(output)
   ```

## Notes

1. **File Paths**:
   - Ensure input file paths are correct.
   - The `nebula_gpu` executable path defaults to `build/bin/nebula_gpu`, if modification is needed, update the path in the script.

2. **Dependencies and Environment**:
   - If `nebula_gpu` requires other dependencies or environment variables, set them before calling.

3. **Error Handling**:
   - If input file does not exist, a `FileNotFoundError` exception will be raised.
   - If `nebula_gpu` execution fails, a `subprocess.CalledProcessError` exception will be raised.

## Future Optimization Suggestions

1. **Logging**:
   - Can add logging functionality to record parameters and execution results for each call.

2. **Performance Optimization**:
   - For frequent calls, consider using multithreading or multiprocessing to optimize performance.

3. **Extended Functionality**:
   - Support more parameters or dynamically configure `nebula_gpu` options.
