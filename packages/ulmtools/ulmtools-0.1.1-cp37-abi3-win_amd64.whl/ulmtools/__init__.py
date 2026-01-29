import numpy as np

from .ulmtools import (
    rs_detect_peaks,
    rs_detect_peaks3d,
    rs_draw_tracks,
    rs_draw_tracks_3d,
)

__all__ = ["detect_peaks", "detect_peaks_3d", "draw_tracks", "draw_tracks_3d"]


def detect_peaks(
    array: np.ndarray,
    threshold: float = float("-inf"),
    min_distance: float = 0.0,
    extent: tuple | None = None,
):
    """
    Find peaks in a 2D image.

    Args:
        array: 2D array-like (coerced to float32) indexed as [x, y]
        extent: Extent object or sequence of 4 floats (x0, x1, y0, y1)
        threshold: Minimum intensity for a peak
        min_distance: Minimum distance between peaks

    Returns:
        indices: Nx2 array of peak indices (x, y)

    Notes:
    - Maxima at the border of the image are ignored.
    - A peak is defined as a pixel with intensity greater than all its neighbors.
    - On equal intensities the pixel with the lowest x is chosen as higher
    - On equal intensities and x the pixel with the lowest y is chosen as higher
    """
    # 1. Automatic Type and Layout Conversion
    # 'C' order ensures the memory is contiguous for Rust/ndarray
    arr = np.ascontiguousarray(array, dtype=np.float32)

    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got {arr.ndim}D")

    if extent is None:
        extent = (0, arr.shape[0] - 1, 0, arr.shape[1] - 1)

    try:
        extent = (
            float(extent[0]),
            float(extent[1]),
            float(extent[2]),
            float(extent[3]),
        )
    except (TypeError, IndexError):
        raise ValueError("Extent must be a sequence of 4 floats (x0, x1, y0, y1)")

    # 3. Call the Rust binary
    return rs_detect_peaks(arr, extent, threshold, min_distance)


def detect_peaks_3d(
    array: np.ndarray,
    threshold: float = float("-inf"),
    min_distance: float = 0.0,
    extent: tuple | None = None,
):
    """
    Find peaks in a 3D image.

    Args:
        array: 3D array-like (coerced to float32) indexed as [x, y, z]
        extent: Extent object or sequence of 6 floats (x0, x1, y0, y1, z0, z1)
        threshold: Minimum intensity for a peak
        min_distance: Minimum distance between peaks

    Returns:
        indices: Nx3 array of peak indices (x, y, z)

    Notes:
    - Maxima at the border of the image are ignored.
    - A peak is defined as a voxel with intensity greater than all its neighbors.
    - On equal intensities the voxel with the lowest x is chosen as higher
    - On equal intensities and x the voxel with the lowest y is chosen as higher
    - On equal intensities, x and y the voxel with the lowest z is chosen as higher
    """
    # 1. Automatic Type and Layout Conversion
    # 'C' order ensures the memory is contiguous for Rust/ndarray
    arr = np.ascontiguousarray(array, dtype=np.float32)

    if arr.ndim != 3:
        raise ValueError(f"Expected 3D array, got {arr.ndim}D")

    if extent is None:
        extent = (0, arr.shape[0] - 1, 0, arr.shape[1] - 1, 0, arr.shape[2] - 1)

    try:
        extent = (
            float(extent[0]),
            float(extent[1]),
            float(extent[2]),
            float(extent[3]),
            float(extent[4]),
            float(extent[5]),
        )
    except (TypeError, IndexError):
        raise ValueError(
            "Extent must be a sequence of 6 floats (x0, x1, y0, y1, z0, z1)"
        )

    # 3. Call the Rust binary
    return rs_detect_peaks3d(arr, extent, threshold, min_distance)


def draw_tracks(
    matrix_x_y_intensity: np.ndarray,
    track_end_indices: np.ndarray,
    extent: tuple,
    pixel_size: float,
    divide_by_pixel_counts: bool = False,
):
    """
    Draw tracks on a 2D image.

    Args:
        matrix_x_y_intensity: 2D array-like (coerced to float32) of shape (N, 3) where
            each row is (x, y, intensity)
        track_end_indices: 1D array-like (coerced to int32) of indices defining where
        extent: Extent object or sequence of 4 floats (x0, x1, y0, y1)
        pixel_size: Pixel size for the output image
        divide_by_pixel_counts: Whether to divide the intensity by the number of hits per pixel

    Returns:
        image: 2D array of drawn tracks
        extent: Tuple of (x0, x1, y0, y1) defining the extent of the output image
    """
    # 1. Automatic Type and Layout Conversion
    # 'C' order ensures the memory is contiguous for Rust/ndarray
    arr = np.ascontiguousarray(matrix_x_y_intensity, dtype=np.float32)
    track_end_indices = np.ascontiguousarray(track_end_indices, dtype=np.int32)

    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got {arr.ndim}D")
    if track_end_indices.ndim != 1:
        raise ValueError(f"Expected 1D array, got {track_end_indices.ndim}D")

    try:
        extent = (
            float(extent[0]),
            float(extent[1]),
            float(extent[2]),
            float(extent[3]),
        )
    except (TypeError, IndexError):
        raise ValueError("Extent must be a sequence of 4 floats (x0, x1, y0, y1)")

    # 3. Call the Rust binary
    return rs_draw_tracks(
        arr, track_end_indices, extent, pixel_size, divide_by_pixel_counts
    )


def draw_tracks_3d(
    matrix_x_y_z_intensity: np.ndarray,
    track_end_indices: np.ndarray,
    extent: tuple,
    pixel_size: float,
    divide_by_voxel_counts: bool = False,
):
    """
    Draw tracks on a 3D image.

    Args:
        matrix_x_y_z_intensity: 2D array-like (coerced to float32) of shape (N, 4) where
            each row is (x, y, z, intensity)
        track_end_indices: 1D array-like (coerced to int32) of indices defining where
        extent: Extent object or sequence of 6 floats (x0, x1, y0, y1, z0, z1)
        pixel_size: Pixel size for the output image
        divide_by_voxel_counts: Whether to divide the intensity by the number of hits per voxel

    Returns:
        image: 3D array of drawn tracks
        extent: Tuple of (x0, x1, y0, y1, z0, z1) defining the extent of the output image
    """
    # 1. Automatic Type and Layout Conversion
    # 'C' order ensures the memory is contiguous for Rust/ndarray
    arr = np.ascontiguousarray(matrix_x_y_z_intensity, dtype=np.float32)
    track_end_indices = np.ascontiguousarray(track_end_indices, dtype=np.int32)

    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got {arr.ndim}D")
    if track_end_indices.ndim != 1:
        raise ValueError(f"Expected 1D array, got {track_end_indices.ndim}D")

    try:
        extent = (
            float(extent[0]),
            float(extent[1]),
            float(extent[2]),
            float(extent[3]),
            float(extent[4]),
            float(extent[5]),
        )
    except (TypeError, IndexError):
        raise ValueError(
            "Extent must be a sequence of 6 floats (x0, x1, y0, y1, z0, z1)"
        )

    # 3. Call the Rust binary
    return rs_draw_tracks_3d(
        arr, track_end_indices, extent, pixel_size, divide_by_voxel_counts
    )
