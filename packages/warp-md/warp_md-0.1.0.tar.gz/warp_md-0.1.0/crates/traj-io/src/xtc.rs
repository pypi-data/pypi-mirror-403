use std::path::PathBuf;

use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::{Box3, FrameChunkBuilder};
use xdrfile::{Frame, Trajectory, XTCTrajectory};

use crate::TrajReader;

pub struct XtcReader {
    traj: XTCTrajectory,
    n_atoms: usize,
    frame: Frame,
    _path: PathBuf,
}

impl XtcReader {
    pub fn open(path: impl Into<PathBuf>) -> TrajResult<Self> {
        let path = path.into();
        let mut traj = XTCTrajectory::open_read(&path).map_err(map_xtc_err)?;
        let n_atoms = traj.get_num_atoms().map_err(map_xtc_err)?;
        let frame = Frame::with_len(n_atoms);
        Ok(Self {
            traj,
            n_atoms,
            frame,
            _path: path,
        })
    }
}

impl TrajReader for XtcReader {
    fn n_atoms(&self) -> usize {
        self.n_atoms
    }

    fn n_frames_hint(&self) -> Option<usize> {
        None
    }

    fn read_chunk(&mut self, max_frames: usize, out: &mut FrameChunkBuilder) -> TrajResult<usize> {
        out.reset(self.n_atoms, max_frames);
        let mut frames = 0;
        while frames < max_frames {
            match self.traj.read(&mut self.frame) {
                Ok(()) => {
                    let box_ = convert_box(self.frame.box_vector);
                    let coords = out.start_frame(box_, Some(self.frame.time));
                    for i in 0..self.n_atoms {
                        let xyz = self.frame.coords[i];
                        coords[i] = [xyz[0] * 10.0, xyz[1] * 10.0, xyz[2] * 10.0, 1.0];
                    }
                    frames += 1;
                }
                Err(err) => {
                    if err.is_eof() {
                        break;
                    }
                    return Err(map_xtc_err(err));
                }
            }
        }
        Ok(frames)
    }
}

fn convert_box(box_vec: [[f32; 3]; 3]) -> Box3 {
    let mut m = [0.0f32; 9];
    for i in 0..3 {
        for j in 0..3 {
            m[i * 3 + j] = box_vec[i][j] * 10.0;
        }
    }
    let tol = 1e-5;
    let is_orth = m[1].abs() < tol
        && m[2].abs() < tol
        && m[3].abs() < tol
        && m[5].abs() < tol
        && m[6].abs() < tol
        && m[7].abs() < tol;
    if is_orth {
        Box3::Orthorhombic {
            lx: m[0],
            ly: m[4],
            lz: m[8],
        }
    } else {
        Box3::Triclinic { m }
    }
}

fn map_xtc_err(err: xdrfile::Error) -> TrajError {
    TrajError::Parse(format!("xtc error: {err}"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use xdrfile::{FileMode, Trajectory};

    #[test]
    fn read_xtc_simple() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("test.xtc");
        let mut traj = XTCTrajectory::open(path.clone(), FileMode::Write).unwrap();
        let mut frame = Frame::with_len(2);
        frame.step = 0;
        frame.time = 2.0;
        frame.box_vector = [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]];
        frame.coords[0] = [0.1, 0.2, 0.3];
        frame.coords[1] = [0.4, 0.5, 0.6];
        traj.write(&frame).unwrap();
        traj.flush().unwrap();

        let mut reader = XtcReader::open(&path).unwrap();
        let mut builder = FrameChunkBuilder::new(2, 2);
        let count = reader.read_chunk(2, &mut builder).unwrap();
        assert_eq!(count, 1);
        let chunk = builder.finish().unwrap();
        assert_eq!(chunk.n_frames, 1);
        assert_eq!(chunk.box_[0], Box3::Orthorhombic { lx: 10.0, ly: 20.0, lz: 30.0 });
        assert!((chunk.coords[0][0] - 1.0).abs() < 1e-6);
    }
}
