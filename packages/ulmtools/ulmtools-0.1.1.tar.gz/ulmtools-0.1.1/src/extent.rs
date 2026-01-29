#![allow(dead_code)]
#![allow(unused_imports)]
#[derive(Debug, Clone, Copy)]
pub struct Extent {
    pub x0: f32,
    pub y0: f32,
    pub x1: f32,
    pub y1: f32,
}

impl Extent {
    pub fn width(&self) -> f32 {
        self.x1 - self.x0
    }

    pub fn height(&self) -> f32 {
        self.y1 - self.y0
    }

    pub fn size_of_dim(&self, dim: usize) -> f32 {
        match dim {
            0 => self.width(),
            1 => self.height(),
            _ => panic!("Extent only has 2 dimensions (0 and 1)"),
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Extent3D {
    pub x0: f32,
    pub x1: f32,
    pub y0: f32,
    pub y1: f32,
    pub z0: f32,
    pub z1: f32,
}
impl Extent3D {
    pub fn width(&self) -> f32 {
        self.x1 - self.x0
    }

    pub fn height(&self) -> f32 {
        self.y1 - self.y0
    }

    pub fn depth(&self) -> f32 {
        self.z1 - self.z0
    }

    pub fn size_of_dim(&self, dim: usize) -> f32 {
        match dim {
            0 => self.width(),
            1 => self.height(),
            2 => self.depth(),
            _ => panic!("Extent3D only has 3 dimensions (0, 1 and 2)"),
        }
    }
}
