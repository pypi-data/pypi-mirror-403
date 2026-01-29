# ulmtools
A collection of tools for Ultrasound Localization Microscopy (ULM) implemented in Rust.

## Installation
```bash
pip install ulmtools
```

# Examples
## Detect peaks in a 2D image
```python
import matplotlib.pyplot as plt
import numpy as np
from ulmtools import detect_peaks

shape = (128, 128)
extent = (0, shape[0] - 1, 0, shape[1] - 1)
image = np.zeros(shape)

# Create test input
x_grid, y_grid = np.meshgrid(
    np.linspace(-1, 1, shape[0]), np.linspace(-1, 1, shape[1]), indexing="ij"
)
for n in range(32):
    x = 2 * (np.random.rand() - 0.5)
    y = 2 * (np.random.rand() - 0.5)
    d = np.sqrt((x_grid - x) ** 2 + (y_grid - y) ** 2)
    image += np.exp(-(d**2 / 3e-3))


peaks, intensities = detect_peaks(image, extent, 0, 0)

# Plot results
fig, ax = plt.subplots()
ax.imshow(
    np.abs(image.T),
    extent=(-0.5, shape[0] - 0.5, -0.5, shape[1] - 0.5),
    origin="lower",
    cmap="hot",
)
ax.scatter(peaks[:, 0], peaks[:, 1], c="blue", s=2)
plt.show()
```

## Draw tracks on a 2D image
```python
import matplotlib.pyplot as plt
import numpy as np
from ulmtools import draw_tracks

shape = (128, 128)
extent = (-1, 1, -1, 1)
pixel_size = 1e-2

t = np.linspace(0.05, 1, 300)
matrix = np.stack(
    [np.sin(5 * 2 * np.pi * t) * t, np.cos(5 * 2 * np.pi * t) * t, 1 - t], axis=1
)

image, extent = draw_tracks(
    matrix,
    track_end_indices=np.array([matrix.shape[0]]),
    extent=extent,
    pixel_size=pixel_size,
    divide_by_pixel_counts=False,
)

fig, ax = plt.subplots()
ax.imshow(
    np.abs(image.T),
    extent=(
        extent[0] - 0.5 * pixel_size,
        extent[1] + 0.5 * pixel_size,
        extent[2] - 0.5 * pixel_size,
        extent[3] + 0.5 * pixel_size,
    ),
    origin="lower",
    cmap="hot",
    interpolation="nearest",
)
plt.show()
```
