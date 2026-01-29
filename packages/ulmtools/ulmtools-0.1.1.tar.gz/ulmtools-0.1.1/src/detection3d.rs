use crate::extent::Extent3D;
use ndarray;
use rayon::prelude::*;

#[derive(Clone)]
struct Peak {
    pub position: Position,
    pub intensity: f32,
}
#[derive(Clone)]
struct Position {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

#[derive(Clone)]
struct Index {
    pub x: isize,
    pub y: isize,
    pub z: isize,
}

pub fn detect_peaks_3d(
    array: &ndarray::ArrayView3<f32>,
    extent: Extent3D,
    threshold: f32,
    min_distance: f32,
) -> (ndarray::Array2<f32>, ndarray::Array1<f32>) {
    let offsets = get_offsets_3x3x3();
    let mut results = find_peaks(array, extent, threshold, &offsets);
    sort_peaks_by_intensity(&mut results);
    let results = discard_close_peaks(&results, min_distance);
    build_output_arrays(&results)
}

fn find_peaks(
    array: &ndarray::ArrayView3<f32>,
    extent: Extent3D,
    threshold: f32,
    offsets: &[Index],
) -> Vec<Peak> {
    let shape = array.shape();

    let indices: Vec<(usize, usize)> =
        itertools::iproduct!(1..shape[0] - 2, 1..shape[1] - 2).collect();

    let results: Vec<Peak> = indices
        .into_par_iter()
        .flat_map(|(x_idx, y_idx)| {
            let mut row_res = Vec::new();
            for z_idx in 1..shape[2] - 2 {
                let index = Index {
                    x: x_idx as isize,
                    y: y_idx as isize,
                    z: z_idx as isize,
                };

                let intensity = index_array_in_bounds(array, &index);
                if intensity < threshold {
                    continue;
                }
                if is_peak_in_neighborhood(array, &index, &offsets) {
                    let position = row_col_to_xyz(&index, shape, &extent);

                    row_res.push(Peak {
                        position,
                        intensity,
                    });
                }
            }

            row_res
        })
        .collect();
    results
}

fn index_array_in_bounds(array: &ndarray::ArrayView3<f32>, index: &Index) -> f32 {
    array[[index.x as usize, index.y as usize, index.z as usize]]
}

fn index_array(array: &ndarray::ArrayView3<f32>, index: &Index) -> Option<f32> {
    array
        .get([index.x as usize, index.y as usize, index.z as usize])
        .copied()
}
fn sort_peaks_by_intensity(peaks: &mut Vec<Peak>) {
    peaks.par_sort_unstable_by(|a, b| {
        b.intensity
            .partial_cmp(&a.intensity)
            .unwrap_or(std::cmp::Ordering::Greater)
    });
}

fn build_output_arrays(peaks: &[Peak]) -> (ndarray::Array2<f32>, ndarray::Array1<f32>) {
    let n_peaks = peaks.len();
    let mut indices: Vec<f32> = Vec::with_capacity(n_peaks * 3);
    let mut intensities: Vec<f32> = Vec::with_capacity(n_peaks);
    for peak in peaks {
        indices.push(peak.position.x);
        indices.push(peak.position.y);
        indices.push(peak.position.z);
        intensities.push(peak.intensity);
    }
    let indices_arr = ndarray::Array2::from_shape_vec((n_peaks, 3), indices).unwrap();
    let intensities_arr = ndarray::Array1::from_shape_vec(n_peaks, intensities).unwrap();
    (indices_arr, intensities_arr)
}

fn is_peak_in_neighborhood(
    array: &ndarray::ArrayView3<f32>,
    index: &Index,
    offsets: &[Index],
) -> bool {
    let intensity = index_array_in_bounds(array, index);
    for offset in offsets {
        let index_other = Index {
            x: (index.x + offset.x),
            y: (index.y + offset.y),
            z: (index.z + offset.z),
        };

        let other_pixel = match index_array(array, &index_other) {
            Some(v) => v,
            None => continue,
        };

        if compare_pixels_a_larger_than_b(other_pixel, &index_other, intensity, &index) {
            return false;
        }
    }
    true
}

fn row_col_to_xyz(index: &Index, shape: &[usize], extent: &Extent3D) -> Position {
    let (n_x, n_y, n_z) = (shape[0] as f32, shape[1] as f32, shape[2] as f32);
    let x = extent.x0 + (index.x as f32) * (extent.x1 - extent.x0) / (n_x - 1.0);
    let y = extent.y0 + (index.y as f32) * (extent.y1 - extent.y0) / (n_y - 1.0);
    let z = extent.z0 + (index.z as f32) * (extent.z1 - extent.z0) / (n_z - 1.0);
    Position { x, y, z }
}

fn compare_pixels_a_larger_than_b(
    intensity_a: f32,
    index_a: &Index,
    intensity_b: f32,
    index_b: &Index,
) -> bool {
    if intensity_a > intensity_b {
        return true;
    }
    if intensity_a < intensity_b {
        return false;
    }
    if index_a.x > index_b.x {
        return true;
    }
    if index_a.x < index_b.x {
        return false;
    }
    if index_a.y > index_b.y {
        return true;
    }

    index_a.z < index_b.z
}

fn get_offsets_nxnxn(n: usize) -> Vec<Index> {
    let mut offsets = Vec::new();
    let n = ((n - 1) / 2) as isize;
    for dx in -n..=n {
        for dy in -n..=n {
            for dz in -n..=n {
                if dx == 0 && dy == 0 && dz == 0 {
                    continue;
                }
                offsets.push(Index {
                    x: dx,
                    y: dy,
                    z: dz,
                });
            }
        }
    }
    offsets
}

fn get_offsets_3x3x3() -> Vec<Index> {
    get_offsets_nxnxn(3)
}

fn discard_close_peaks(peaks: &Vec<Peak>, min_distance: f32) -> Vec<Peak> {
    let mut filtered_peaks: Vec<Peak> = Vec::new();
    let min_distance_squared = min_distance * min_distance;
    for peak in peaks.iter() {
        if is_too_close_to_existing_peaks(peak, &filtered_peaks, min_distance_squared) {
            continue;
        }
        filtered_peaks.push((*peak).to_owned());
    }
    filtered_peaks
}

fn is_too_close_to_existing_peaks(
    peak: &Peak,
    existing_peaks: &[Peak],
    min_distance_squared: f32,
) -> bool {
    for existing_peak in existing_peaks {
        let dist_sq = compute_distance_squared(&peak.position, &existing_peak.position);
        if dist_sq < min_distance_squared {
            return true;
        }
    }
    false
}

fn compute_distance_squared(a: &Position, b: &Position) -> f32 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    let dz = a.z - b.z;
    dx * dx + dy * dy + dz * dz
}
