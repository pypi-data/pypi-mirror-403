use crate::error::{TrajError, TrajResult};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Box3 {
    None,
    Orthorhombic { lx: f32, ly: f32, lz: f32 },
    Triclinic { m: [f32; 9] },
}

#[derive(Debug, Clone)]
pub struct FrameChunk {
    pub n_atoms: usize,
    pub n_frames: usize,
    pub coords: Vec<[f32; 4]>,
    pub box_: Vec<Box3>,
    pub time_ps: Option<Vec<f32>>,
}

#[derive(Debug)]
pub struct FrameChunkBuilder {
    n_atoms: usize,
    coords_buf: Vec<[f32; 4]>,
    box_buf: Vec<Box3>,
    time_buf: Vec<f32>,
    time_enabled: bool,
}

impl FrameChunkBuilder {
    pub fn new(n_atoms: usize, max_frames: usize) -> Self {
        Self {
            n_atoms,
            coords_buf: Vec::with_capacity(n_atoms * max_frames),
            box_buf: Vec::with_capacity(max_frames),
            time_buf: Vec::with_capacity(max_frames),
            time_enabled: false,
        }
    }

    pub fn reset(&mut self, n_atoms: usize, max_frames: usize) {
        self.n_atoms = n_atoms;
        self.coords_buf.clear();
        self.box_buf.clear();
        self.time_buf.clear();
        self.time_enabled = false;
        self.coords_buf.reserve(n_atoms * max_frames);
        self.box_buf.reserve(max_frames);
        self.time_buf.reserve(max_frames);
    }

    pub fn start_frame(&mut self, box_: Box3, time_ps: Option<f32>) -> &mut [[f32; 4]] {
        let frame_index = self.box_buf.len();
        self.box_buf.push(box_);
        match time_ps {
            Some(t) => {
                self.time_buf.push(t);
                self.time_enabled = true;
            }
            None => {
                if self.time_enabled {
                    self.time_buf.push(0.0);
                }
            }
        }
        let start = frame_index * self.n_atoms;
        let end = start + self.n_atoms;
        if self.coords_buf.len() < end {
            self.coords_buf.resize(end, [0.0; 4]);
        }
        &mut self.coords_buf[start..end]
    }

    pub fn finish(&mut self) -> TrajResult<FrameChunk> {
        let n_frames = self.box_buf.len();
        if self.coords_buf.len() != n_frames * self.n_atoms {
            return Err(TrajError::Parse("frame chunk buffer size mismatch".into()));
        }
        let coords = self.coords_buf.clone();
        let box_ = self.box_buf.clone();
        let time_ps = if self.time_enabled {
            Some(self.time_buf.clone())
        } else {
            None
        };
        Ok(FrameChunk {
            n_atoms: self.n_atoms,
            n_frames,
            coords,
            box_,
            time_ps,
        })
    }
}
