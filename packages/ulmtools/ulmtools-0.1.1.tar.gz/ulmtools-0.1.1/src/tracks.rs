use crate::extent::Extent;
use crate::image::Shape;

pub struct FloatTrackPoint {
    pub x_pos: f32,
    pub y_pos: f32,
    pub intensity: f32,
}

pub struct TrackPoint {
    pub x_pos: i32,
    pub y_pos: i32,
    pub intensity: f32,
}

pub struct FloatTrack {
    points: Vec<FloatTrackPoint>,
}

pub struct Track {
    pub points: Vec<TrackPoint>,
}

impl Track {
    /// Remove consecutive duplicate points
    pub fn reduced(mut self) -> Self {
        self.points
            .dedup_by(|a, b| a.x_pos == b.x_pos && a.y_pos == b.y_pos);
        self
    }
}

impl FloatTrack {
    pub fn new() -> Self {
        FloatTrack { points: Vec::new() }
    }

    pub fn to_track(&self, extent: Extent, shape: Shape) -> Track {
        Track {
            points: self
                .points
                .iter()
                .map(|p| TrackPoint {
                    x_pos: (((p.x_pos - extent.x0) / (extent.x1 - extent.x0) * shape.n_x as f32)
                        .round()) as i32,
                    y_pos: (((p.y_pos - extent.y0) / (extent.y1 - extent.y0) * shape.n_y as f32)
                        .round()) as i32,
                    intensity: p.intensity,
                })
                .collect(),
        }
    }

    pub fn from_matrices(
        tracks_array: &ndarray::ArrayView2<f32>,
        split_indices_array: &ndarray::ArrayView1<i32>,
    ) -> Vec<FloatTrack> {
        let tracks_n_rows = tracks_array.shape()[0];

        let mut tracks = Vec::new();
        let mut start_idx = 0;
        for end_idx in split_indices_array.iter().map(|&x| x as usize) {
            let mut new_track = FloatTrack::new();

            for m in start_idx..end_idx {
                if m >= tracks_n_rows {
                    continue;
                }
                new_track.points.push(FloatTrackPoint {
                    x_pos: tracks_array[[m, 0]],
                    y_pos: tracks_array[[m, 1]],
                    intensity: tracks_array[[m, 2]],
                });
            }
            tracks.push(new_track);
            start_idx = end_idx;
        }
        tracks
    }
}

impl std::fmt::Debug for FloatTrack {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "FloatTrack with {} points", self.points.len())
    }
}
