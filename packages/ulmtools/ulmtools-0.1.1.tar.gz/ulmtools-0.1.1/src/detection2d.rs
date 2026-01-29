use crate::extent::Extent;
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
}
#[derive(Clone)]
struct Index {
    pub x: isize,
    pub y: isize,
}

pub fn detect_peaks(
    array: &ndarray::ArrayView2<f32>,
    extent: Extent,
    threshold: f32,
    min_distance: f32,
) -> (ndarray::Array2<f32>, ndarray::Array1<f32>) {
    let offsets = get_offsets_3x3_excluding_center();
    let mut results = find_peaks(array, extent, threshold, &offsets);
    sort_peaks_by_intensity(&mut results);
    let filtered_results = discard_close_peaks(&results, min_distance);
    build_output_arrays(&filtered_results)
}

fn find_peaks(
    array: &ndarray::ArrayView2<f32>,
    extent: Extent,
    threshold: f32,
    offsets: &[Index],
) -> Vec<Peak> {
    let shape = array.shape();
    // parallel iterate over rows, build a Vec<(row, col, intensity)>
    let results: Vec<Peak> = (1..shape[0] - 1)
        .into_par_iter() // rayon parallel iterator
        .flat_map(|x_idx| {
            let mut result_all_y = Vec::new();
            for y_idx in 1..shape[1] - 1 {
                let index = Index {
                    x: x_idx as isize,
                    y: y_idx as isize,
                };

                let intensity = index_array_in_bounds(array, &index);
                if intensity < threshold {
                    continue;
                }

                if is_peak_in_neighborhood(array, &index, &offsets) {
                    let (x, y) = index_to_xy(&index, shape, extent);

                    result_all_y.push(Peak {
                        position: Position { x, y },
                        intensity,
                    });
                }
            }
            result_all_y
        })
        .collect();
    results
}

fn sort_peaks_by_intensity(peaks: &mut Vec<Peak>) {
    peaks.par_sort_unstable_by(|a, b| {
        b.intensity
            .partial_cmp(&a.intensity)
            .unwrap_or(std::cmp::Ordering::Greater)
    });
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

fn build_output_arrays(peaks: &[Peak]) -> (ndarray::Array2<f32>, ndarray::Array1<f32>) {
    let n_peaks = peaks.len();
    let mut indices: Vec<f32> = Vec::with_capacity(n_peaks * 2);
    let mut intensities: Vec<f32> = Vec::with_capacity(n_peaks);
    for peak in peaks {
        indices.push(peak.position.x);
        indices.push(peak.position.y);
        intensities.push(peak.intensity);
    }
    let indices_arr = ndarray::Array2::from_shape_vec((n_peaks, 2), indices).unwrap();
    let intensities_arr = ndarray::Array1::from_shape_vec(n_peaks, intensities).unwrap();
    (indices_arr, intensities_arr)
}

fn is_peak_in_neighborhood(
    array: &ndarray::ArrayView2<f32>,
    index: &Index,
    offsets: &[Index],
) -> bool {
    let intensity = index_array_in_bounds(array, &index);
    for offset in offsets {
        let index_other = Index {
            x: index.x + offset.x,
            y: index.y + offset.y,
        };

        let other_pixel = match index_array(array, &index_other) {
            Some(val) => val,
            None => continue,
        };

        if compare_pixels_a_larger_than_b(other_pixel, &index_other, intensity, &index) {
            return false;
        }
    }
    true
}

fn index_array_in_bounds(array: &ndarray::ArrayView2<f32>, index: &Index) -> f32 {
    array[[index.x as usize, index.y as usize]]
}

fn index_array(array: &ndarray::ArrayView2<f32>, index: &Index) -> Option<f32> {
    array.get([index.x as usize, index.y as usize]).copied()
}

fn index_to_xy(index: &Index, shape: &[usize], extent: Extent) -> (f32, f32) {
    let (n_x, n_y) = (shape[0] as f32, shape[1] as f32);
    let x = extent.x0 + (index.x as f32) * (extent.width() / (n_x - 1.0));
    let y = extent.y0 + (index.y as f32) * (extent.height() / (n_y - 1.0));
    (x, y)
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
    index_a.y > index_b.y
}

fn get_offsets_3x3_excluding_center() -> Vec<Index> {
    let mut offsets = Vec::new();
    for dx in -1..=1 {
        for dy in -1..=1 {
            if dx == 0 && dy == 0 {
                continue;
            }
            offsets.push(Index { x: dx, y: dy });
        }
    }
    offsets
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
    dx * dx + dy * dy
}
