#![allow(dead_code)]
extern crate line_drawing;
use crate::extent::Extent3D;
use line_drawing::Bresenham3d;
#[derive(Debug, Clone, Copy)]
pub struct Shape {
    pub n_x: usize,
    pub n_y: usize,
    pub n_z: usize,
}

pub struct Image {
    values: Vec<f32>,
    pixel_counts: Vec<u32>,
    shape: Shape,
}

impl Image {
    pub fn new(shape: Shape) -> Self {
        let total_pixels = shape.n_x * shape.n_y * shape.n_z;
        Image {
            values: vec![0.0; total_pixels],
            pixel_counts: vec![0; total_pixels],
            shape,
        }
    }

    fn get_index(&self, x_idx: usize, y_idx: usize, z_idx: usize) -> usize {
        z_idx + y_idx * self.shape.n_z + x_idx * self.shape.n_y * self.shape.n_z
    }

    pub fn shape(&self) -> Shape {
        self.shape
    }

    pub fn data(&self) -> &[f32] {
        &self.values
    }

    pub fn get_value(&self, x_idx: usize, y_idx: usize, z_idx: usize) -> f32 {
        let idx = self.get_index(x_idx, y_idx, z_idx);
        if idx >= self.shape.n_y * self.shape.n_x * self.shape.n_z {
            return 0.0;
        }
        self.values[idx]
    }

    pub fn get_pixel_count(&self, x_idx: usize, y_idx: usize, z_idx: usize) -> u32 {
        let idx = self.get_index(x_idx, y_idx, z_idx);
        if idx >= self.shape.n_y * self.shape.n_x * self.shape.n_z {
            return 0;
        }

        self.pixel_counts[idx]
    }

    pub fn add_value(&mut self, x_idx: usize, y_idx: usize, z_idx: usize, value: f32) {
        if value.is_nan() {
            return;
        }

        if x_idx >= self.shape.n_x || y_idx >= self.shape.n_y || z_idx >= self.shape.n_z {
            return;
        }

        let idx = self.get_index(x_idx, y_idx, z_idx);
        self.values[idx] += value;
        self.pixel_counts[idx] += 1;
    }

    pub fn add_track(&mut self, track: &crate::tracks3d::Track) {
        let n_points = track.points.len();

        if n_points == 0 {
            return;
        }

        for track_point in 0..n_points - 1 {
            let point0 = &track.points[track_point];
            let point1 = &track.points[track_point + 1];

            let start_point = (point0.x_pos, point0.y_pos, point0.z_pos);
            let end_point = (point1.x_pos, point1.y_pos, point1.z_pos);

            let n_points = Bresenham3d::new(start_point, end_point).count() + 1;

            for (n, (x, y, z)) in Bresenham3d::new(start_point, end_point)
                .into_iter()
                .enumerate()
            {
                if x < 0 || y < 0 || z < 0 {
                    continue;
                }
                let denom = n_points as f32 - 1.0;
                let alpha = if denom != 0.0 {
                    (n as f32) / denom
                } else {
                    0.0
                };
                let intensity = point0.intensity * (1.0 - alpha) + point1.intensity * alpha;
                self.add_value(x as usize, y as usize, z as usize, intensity);
            }
        }

        self.add_value(
            track.points.last().unwrap().x_pos as usize,
            track.points.last().unwrap().y_pos as usize,
            track.points.last().unwrap().z_pos as usize,
            track.points.last().unwrap().intensity,
        );
    }

    pub fn display(&self) {
        for y_idx in 0..self.shape.n_y {
            for x_idx in 0..self.shape.n_x {
                for z_idx in 0..self.shape.n_z {
                    let idx = self.get_index(x_idx, y_idx, z_idx);
                    print!("{:.1} ", self.values[idx]);
                }
            }
            println!();
        }
    }

    pub fn divide_pixel_counts(&mut self) {
        for i in 0..self.values.len() {
            if self.pixel_counts[i] > 0 {
                self.values[i] /= self.pixel_counts[i] as f32;
            }
        }
    }

    pub fn to_pyarray(
        self,
        py: pyo3::Python<'_>,
    ) -> pyo3::PyResult<pyo3::Bound<'_, numpy::PyArray3<f32>>> {
        let owned_array = match ndarray::Array3::from_shape_vec(
            (self.shape.n_x, self.shape.n_y, self.shape.n_z),
            self.values,
        ) {
            Ok(arr) => arr,
            Err(err) => {
                return Err(pyo3::PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Error creating ndarray: {}", err),
                ))
            }
        };
        let array = numpy::PyArray3::from_owned_array(py, owned_array);
        Ok(array.into())
    }
}

impl Extent3D {
    pub fn get_shape_and_extent(&self, pixel_size: f32) -> (Shape, Self) {
        let mut extent = self.clone();

        let n_x = ((extent.x1 - extent.x0 + pixel_size * 0.999) / pixel_size) as usize;
        let n_y = ((extent.y1 - extent.y0 + pixel_size * 0.999) / pixel_size) as usize;
        let n_z = ((extent.z1 - extent.z0 + pixel_size * 0.999) / pixel_size) as usize;

        extent.x1 = extent.x0 + n_x as f32 * pixel_size;
        extent.y1 = extent.y0 + n_y as f32 * pixel_size;
        extent.z1 = extent.z0 + n_z as f32 * pixel_size;

        let shape = Shape { n_x, n_y, n_z };

        (shape, extent)
    }
}
