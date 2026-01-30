# [**gdutils**](https://gdutils-a2ef81.gitlabpages.inria.fr/)

**gdutils** is a lightweight Python utility library. It provides tools for organized file management, clean logging, and quality plotting.

## Installation

```bash
pip install gd-py-utils
```

## Quick Start

### 1. Path Management (`fPath`)
Easily create paths relative to your script's location, ensuring portability.

```python
import gdutils as gd

# Create an 'out' directory next to this script
out_dir = gd.fPath(__file__, "out", mkdir=True)
# -> /path/to/script_dir/out/
```

### 2. Data Management (`Container`)
A `Container` manages a directory and maintains a **logical registry** of your files.

```python
import numpy as np
import gdutils as gd

# Create a managed directory
out = gd.fPath(__file__, "out")
with gd.Container(out / "experiments/run_01", clean=True) as ct:
    
    # Create file paths naturally (automatically registered by stem name)
    data_file = ct / "data/results.npy"
    np.save(data_file, np.random.randn(100))

# Access files later using their logical key (filename without extension)
print(ct.results)  
# -> /abs/path/to/experiments/run_01/data/results.npy
```

### 3. Plotting Helpers (`SPlot`)

```python
import matplotlib.pyplot as plt

# Context manager handles plt.show() or saving automatically
with gd.SPlot(fname=ct / "my_plot.png", show=False):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], label="Data")
```

### 4. Logging
Get clean, readable logs with minimal setup.

```python
log = gd.get_logger()
log.info("Experiment started")
# [INFO] Experiment started
```

## Features

- **DataContainer**: Persistent key-value registry for filesystem paths.
- **TempContainer**: Automatic temporary directory cleanup.
- **Plotting**: `despine`, `move_legend`, `get_color_cycle`, and `SPlot` context manager.
- **Logging**: Zero-config formatted logger.
- **IO**: Path manipulation helpers (`fPath`).
