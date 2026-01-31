pub mod dcd;
pub mod gro;
pub mod pdb;
pub mod xtc;

use traj_core::error::TrajResult;
use traj_core::frame::FrameChunkBuilder;
use traj_core::system::System;

pub trait TopologyReader {
    fn read_system(&mut self) -> TrajResult<System>;
}

pub trait TrajReader {
    fn n_atoms(&self) -> usize;
    fn n_frames_hint(&self) -> Option<usize>;
    fn read_chunk(&mut self, max_frames: usize, out: &mut FrameChunkBuilder) -> TrajResult<usize>;
}
