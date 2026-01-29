use crate::extent::{Extent, Extent3D};
use crate::image::Image;
use numpy::{
    IntoPyArray, PyArray1, PyArray2, PyArray3, PyReadonlyArray1, PyReadonlyArray2, PyReadonlyArray3,
};
use pyo3::prelude::*;
use pyo3::{pymodule, types::PyModule, types::PyTuple, Bound, PyResult, Python};
mod detection2d;
mod detection3d;
mod extent;
mod image;
mod image3d;
mod tracks;
mod tracks3d;

#[pyfunction]
fn rs_detect_peaks<'py>(
    py: Python<'py>,
    array: PyReadonlyArray2<'py, f32>,
    extent: Bound<'_, PyTuple>,
    threshold: f32,
    min_distance: f32,
) -> PyResult<(Bound<'py, PyArray2<f32>>, Bound<'py, PyArray1<f32>>)> {
    let array = array.as_array();
    let shape = array.shape();

    if shape.len() != 2 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Input array must be 2D",
        ));
    }

    let extent = Extent {
        x0: extent.get_item(0)?.extract()?,
        x1: extent.get_item(1)?.extract()?,
        y0: extent.get_item(2)?.extract()?,
        y1: extent.get_item(3)?.extract()?,
    };

    let (indices_arr, intensities_arr) =
        detection2d::detect_peaks(&array, extent, threshold, min_distance);

    Ok((
        indices_arr.into_pyarray(py).to_owned(),
        intensities_arr.into_pyarray(py).to_owned(),
    ))
}

#[pyfunction]
fn rs_detect_peaks3d<'py>(
    py: Python<'py>,
    array: PyReadonlyArray3<'py, f32>,
    extent: Bound<'_, PyTuple>,
    threshold: f32,
    min_distance: f32,
) -> PyResult<(Bound<'py, PyArray2<f32>>, Bound<'py, PyArray1<f32>>)> {
    let array = array.as_array();
    let shape = array.shape();

    if shape.len() != 3 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Input array must be 3D",
        ));
    }

    let extent = Extent3D {
        x0: extent.get_item(0)?.extract()?,
        x1: extent.get_item(1)?.extract()?,
        y0: extent.get_item(2)?.extract()?,
        y1: extent.get_item(3)?.extract()?,
        z0: extent.get_item(4)?.extract()?,
        z1: extent.get_item(5)?.extract()?,
    };

    let (indices_arr, intensities_arr) =
        detection3d::detect_peaks_3d(&array, extent, threshold, min_distance);

    Ok((
        indices_arr.into_pyarray(py).to_owned(),
        intensities_arr.into_pyarray(py).to_owned(),
    ))
}

#[pyfunction]
fn rs_draw_tracks<'py>(
    py: Python<'py>,
    matrix_x_y_intensity: PyReadonlyArray2<'py, f32>,
    track_end_indices: PyReadonlyArray1<'py, i32>,
    extent: Bound<'_, PyTuple>,
    pixel_size: f32,
    divide_by_pixel_counts: bool,
) -> PyResult<(Bound<'py, PyArray2<f32>>, (f32, f32, f32, f32))> {
    let extent = Extent {
        x0: extent.get_item(0)?.extract()?,
        x1: extent.get_item(1)?.extract()?,
        y0: extent.get_item(2)?.extract()?,
        y1: extent.get_item(3)?.extract()?,
    };

    let (shape, extent) = extent.get_shape_and_new_extent(pixel_size);

    let tracks = tracks::FloatTrack::from_matrices(
        &matrix_x_y_intensity.as_array(),
        &track_end_indices.as_array(),
    );

    let tracks = tracks
        .iter()
        .map(|t| t.to_track(extent, shape).reduced())
        .collect::<Vec<tracks::Track>>();

    let mut image = Image::new(shape);

    for track in &tracks {
        image.add_track(track);
    }

    if divide_by_pixel_counts {
        image.divide_pixel_counts();
    }
    let image = image.to_pyarray(py)?;

    Ok((image, (extent.x0, extent.x1, extent.y0, extent.y1)))
}

#[pyfunction]
fn rs_draw_tracks_3d<'py>(
    py: Python<'py>,
    matrix_x_y_z_intensity: PyReadonlyArray2<'py, f32>,
    track_end_indices: PyReadonlyArray1<'py, i32>,
    extent: Bound<'_, PyTuple>,
    pixel_size: f32,
    divide_by_pixel_counts: bool,
) -> PyResult<(Bound<'py, PyArray3<f32>>, (f32, f32, f32, f32, f32, f32))> {
    let extent: Extent3D = Extent3D {
        x0: extent.get_item(0)?.extract()?,
        x1: extent.get_item(1)?.extract()?,
        y0: extent.get_item(2)?.extract()?,
        y1: extent.get_item(3)?.extract()?,
        z0: extent.get_item(4)?.extract()?,
        z1: extent.get_item(5)?.extract()?,
    };

    let (shape, extent) = extent.get_shape_and_extent(pixel_size);

    let tracks = tracks3d::FloatTrack::from_matrices(
        &matrix_x_y_z_intensity.as_array(),
        &track_end_indices.as_array(),
    );

    let tracks = tracks
        .iter()
        .map(|t| t.to_track(extent, shape).reduced())
        .collect::<Vec<tracks3d::Track>>();

    let mut image = image3d::Image::new(shape);

    for track in &tracks {
        image.add_track(track);
    }

    if divide_by_pixel_counts {
        image.divide_pixel_counts();
    }
    let image = image.to_pyarray(py)?;

    Ok((
        image,
        (
            extent.x0, extent.x1, extent.y0, extent.y1, extent.z0, extent.z1,
        ),
    ))
}

#[pymodule]
fn ulmtools(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rs_detect_peaks, m)?)?;
    m.add_function(wrap_pyfunction!(rs_detect_peaks3d, m)?)?;
    m.add_function(wrap_pyfunction!(rs_draw_tracks, m)?)?;
    m.add_function(wrap_pyfunction!(rs_draw_tracks_3d, m)?)?;
    Ok(())
}
