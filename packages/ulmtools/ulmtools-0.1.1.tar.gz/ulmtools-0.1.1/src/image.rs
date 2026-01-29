#![allow(dead_code)]
extern crate bresenham;
use crate::extent::Extent;
use bresenham::Bresenham;

#[derive(Debug, Clone, Copy)]
pub struct Shape {
    pub n_x: usize,
    pub n_y: usize,
}

pub struct Image {
    values: Vec<f32>,
    pixel_counts: Vec<u32>,
    shape: Shape,
}

impl Image {
    pub fn new(shape: Shape) -> Self {
        let total_pixels = shape.n_x * shape.n_y;
        Image {
            values: vec![0.0; total_pixels],
            pixel_counts: vec![0; total_pixels],
            shape,
        }
    }

    fn get_index(&self, x_idx: usize, y_idx: usize) -> usize {
        y_idx + x_idx * self.shape.n_y
    }

    pub fn shape(&self) -> Shape {
        self.shape
    }

    pub fn data(&self) -> &[f32] {
        &self.values
    }

    pub fn get_value(&self, x_idx: usize, y_idx: usize) -> f32 {
        let idx = self.get_index(x_idx, y_idx);
        if idx >= self.shape.n_y * self.shape.n_x {
            return 0.0;
        }
        self.values[idx]
    }

    pub fn get_pixel_count(&self, x_idx: usize, y_idx: usize) -> u32 {
        let idx = self.get_index(x_idx, y_idx);
        if idx >= self.shape.n_y * self.shape.n_x {
            return 0;
        }

        self.pixel_counts[idx]
    }

    pub fn add_value(&mut self, x_idx: usize, y_idx: usize, value: f32) {
        if value.is_nan() {
            return;
        }

        if x_idx >= self.shape.n_x || y_idx >= self.shape.n_y {
            return;
        }

        let idx = self.get_index(x_idx, y_idx);
        self.values[idx] += value;
        self.pixel_counts[idx] += 1;
    }

    pub fn add_track(&mut self, track: &crate::tracks::Track) {
        let n_points = track.points.len();

        if n_points == 0 {
            return;
        }

        for track_point in 0..n_points - 1 {
            let point0 = &track.points[track_point];
            let point1 = &track.points[track_point + 1];

            let start_point = (point0.x_pos as isize, point0.y_pos as isize);
            let end_point = (point1.x_pos as isize, point1.y_pos as isize);

            let n_points = Bresenham::new(start_point, end_point).count() + 1;

            for (n, (x, y)) in Bresenham::new(start_point, end_point)
                .into_iter()
                .enumerate()
            {
                let denom = n_points as f32 - 1.0;
                let alpha = if denom != 0.0 {
                    (n as f32) / denom
                } else {
                    0.0
                };
                let intensity = point0.intensity * (1.0 - alpha) + point1.intensity * alpha;
                self.add_value(x as usize, y as usize, intensity);
            }
        }

        self.add_value(
            track.points.last().unwrap().x_pos as usize,
            track.points.last().unwrap().y_pos as usize,
            track.points.last().unwrap().intensity,
        );
    }

    pub fn display(&self) {
        for y_idx in 0..self.shape.n_y {
            for x_idx in 0..self.shape.n_x {
                let idx = self.get_index(x_idx, y_idx);
                print!("{:.1} ", self.values[idx]);
            }
            println!();
        }
    }

    pub fn divide_pixel_counts(&mut self) {
        for i in 0..self.values.len() {
            if self.pixel_counts[i] > 0 {
                self.values[i] /= (self.pixel_counts[i] as f32).max(10.0);
            }
        }
    }

    pub fn to_pyarray(
        self,
        py: pyo3::Python<'_>,
    ) -> pyo3::PyResult<pyo3::Bound<'_, numpy::PyArray2<f32>>> {
        let owned_array =
            match ndarray::Array2::from_shape_vec((self.shape.n_x, self.shape.n_y), self.values) {
                Ok(arr) => arr,
                Err(err) => {
                    return Err(pyo3::PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        format!("Error creating ndarray: {}", err),
                    ))
                }
            };
        let array = numpy::PyArray2::from_owned_array(py, owned_array);
        Ok(array.into())
    }
}

impl Extent {
    pub fn get_shape_and_new_extent(&self, pixel_size: f32) -> (Shape, Self) {
        let mut extent = self.clone();

        let n_x = ((extent.x1 - extent.x0 + pixel_size * 0.999) / pixel_size) as usize;
        let n_y = ((extent.y1 - extent.y0 + pixel_size * 0.999) / pixel_size) as usize;

        extent.x1 = extent.x0 + n_x as f32 * pixel_size;
        extent.y1 = extent.y0 + n_y as f32 * pixel_size;

        let shape = Shape { n_x, n_y };

        (shape, extent)
    }
}
