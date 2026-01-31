use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::PathBuf;

use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::{Box3, FrameChunkBuilder};

use crate::TrajReader;

#[derive(Debug, Clone, Copy)]
enum Endian {
    Little,
    Big,
}

#[derive(Debug)]
pub struct DcdReader {
    file: File,
    endian: Endian,
    marker_size: usize,
    n_atoms: usize,
    n_frames: Option<usize>,
    length_scale: f32,
}

impl DcdReader {
    pub fn open(path: impl Into<PathBuf>, length_scale: f32) -> TrajResult<Self> {
        let path = path.into();
        let mut file = File::open(&path)?;
        let (endian, marker_size, header_len) = detect_header_marker(&mut file)?;
        let header_len_usize = usize::try_from(header_len).map_err(|_| {
            TrajError::Parse("DCD header length too large".into())
        })?;
        let mut header = vec![0u8; header_len_usize];
        file.read_exact(&mut header)?;
        let trailer = read_marker(&mut file, endian, marker_size)?;
        if trailer != header_len {
            return Err(TrajError::Parse("DCD header record length mismatch".into()));
        }

        // Skip title record
        skip_record(&mut file, endian, marker_size)?;

        // Read natoms record
        let natoms_len = read_marker(&mut file, endian, marker_size)?;
        if natoms_len != 4 {
            return Err(TrajError::Parse("unexpected natoms record length".into()));
        }
        let natoms = read_i32(&mut file, endian)?;
        let natoms_end = read_marker(&mut file, endian, marker_size)?;
        if natoms_end != natoms_len {
            return Err(TrajError::Parse("natoms record length mismatch".into()));
        }
        if natoms <= 0 {
            return Err(TrajError::Parse("invalid natoms".into()));
        }

        Ok(Self {
            file,
            endian,
            marker_size,
            n_atoms: natoms as usize,
            n_frames: None,
            length_scale,
        })
    }
}

impl TrajReader for DcdReader {
    fn n_atoms(&self) -> usize {
        self.n_atoms
    }

    fn n_frames_hint(&self) -> Option<usize> {
        self.n_frames
    }

    fn read_chunk(&mut self, max_frames: usize, out: &mut FrameChunkBuilder) -> TrajResult<usize> {
        out.reset(self.n_atoms, max_frames);
        let mut frames = 0;
        while frames < max_frames {
            match self.read_frame(out)? {
                true => frames += 1,
                false => break,
            }
        }
        Ok(frames)
    }
}

impl DcdReader {
    fn read_frame(&mut self, out: &mut FrameChunkBuilder) -> TrajResult<bool> {
        let expected_len = (self.n_atoms * 4) as u64;
        let mut len = match read_marker_opt(&mut self.file, self.endian, self.marker_size)? {
            Some(l) => l,
            None => return Ok(false),
        };

        let mut box_ = Box3::None;
        if len != expected_len {
            if is_unitcell_len(len) {
                box_ = read_unitcell_with_len(
                    &mut self.file,
                    self.endian,
                    self.marker_size,
                    len,
                    self.length_scale,
                )?;
                len = match read_marker_opt(&mut self.file, self.endian, self.marker_size)? {
                    Some(l) => l,
                    None => return Ok(false),
                };
            }
        }

        if len != expected_len {
            return Err(TrajError::Parse("unexpected DCD coordinate record length".into()));
        }
        let x = read_f32_record_with_len(
            &mut self.file,
            self.endian,
            self.marker_size,
            self.n_atoms,
            len,
        )?;
        let y = read_f32_record(&mut self.file, self.endian, self.marker_size, self.n_atoms)?;
        let z = read_f32_record(&mut self.file, self.endian, self.marker_size, self.n_atoms)?;

        let coords = out.start_frame(box_, None);
        for i in 0..self.n_atoms {
            coords[i] = [
                x[i] * self.length_scale,
                y[i] * self.length_scale,
                z[i] * self.length_scale,
                1.0,
            ];
        }
        Ok(true)
    }
}

fn detect_header_marker(file: &mut File) -> TrajResult<(Endian, usize, u64)> {
    let mut buf = [0u8; 8];
    file.read_exact(&mut buf)?;
    let len64_le = u64::from_le_bytes(buf);
    let len64_be = u64::from_be_bytes(buf);
    if is_header_len_u64(len64_le) {
        return Ok((Endian::Little, 8, len64_le));
    }
    if is_header_len_u64(len64_be) {
        return Ok((Endian::Big, 8, len64_be));
    }
    file.seek(SeekFrom::Start(0))?;
    let mut buf4 = [0u8; 4];
    file.read_exact(&mut buf4)?;
    let len_le = u32::from_le_bytes(buf4);
    let len_be = u32::from_be_bytes(buf4);
    if is_header_len(len_le) {
        Ok((Endian::Little, 4, len_le as u64))
    } else if is_header_len(len_be) {
        Ok((Endian::Big, 4, len_be as u64))
    } else {
        Err(TrajError::Unsupported(
            "unsupported DCD record marker".into(),
        ))
    }
}

fn is_header_len(len: u32) -> bool {
    matches!(len, 84 | 164)
}

fn is_header_len_u64(len: u64) -> bool {
    matches!(len, 84 | 164)
}

fn is_unitcell_len(len: u64) -> bool {
    matches!(len, 48 | 24)
}

fn read_marker(file: &mut File, endian: Endian, marker_size: usize) -> TrajResult<u64> {
    match marker_size {
        4 => {
            let mut buf = [0u8; 4];
            file.read_exact(&mut buf)?;
            Ok(match endian {
                Endian::Little => u32::from_le_bytes(buf) as u64,
                Endian::Big => u32::from_be_bytes(buf) as u64,
            })
        }
        8 => {
            let mut buf = [0u8; 8];
            file.read_exact(&mut buf)?;
            Ok(match endian {
                Endian::Little => u64::from_le_bytes(buf),
                Endian::Big => u64::from_be_bytes(buf),
            })
        }
        _ => Err(TrajError::Unsupported(
            "unsupported DCD marker size".into(),
        )),
    }
}

fn read_marker_opt(
    file: &mut File,
    endian: Endian,
    marker_size: usize,
) -> TrajResult<Option<u64>> {
    let mut buf = vec![0u8; marker_size];
    match file.read_exact(&mut buf) {
        Ok(()) => {
            let len = match marker_size {
                4 => {
                    let mut arr = [0u8; 4];
                    arr.copy_from_slice(&buf);
                    match endian {
                        Endian::Little => u32::from_le_bytes(arr) as u64,
                        Endian::Big => u32::from_be_bytes(arr) as u64,
                    }
                }
                8 => {
                    let mut arr = [0u8; 8];
                    arr.copy_from_slice(&buf);
                    match endian {
                        Endian::Little => u64::from_le_bytes(arr),
                        Endian::Big => u64::from_be_bytes(arr),
                    }
                }
                _ => {
                    return Err(TrajError::Unsupported(
                        "unsupported DCD marker size".into(),
                    ))
                }
            };
            Ok(Some(len))
        }
        Err(err) if err.kind() == std::io::ErrorKind::UnexpectedEof => Ok(None),
        Err(err) => Err(err.into()),
    }
}

fn read_i32(file: &mut File, endian: Endian) -> TrajResult<i32> {
    let mut buf = [0u8; 4];
    file.read_exact(&mut buf)?;
    Ok(match endian {
        Endian::Little => i32::from_le_bytes(buf),
        Endian::Big => i32::from_be_bytes(buf),
    })
}

fn read_f32(file: &mut File, endian: Endian) -> TrajResult<f32> {
    let mut buf = [0u8; 4];
    file.read_exact(&mut buf)?;
    Ok(match endian {
        Endian::Little => f32::from_le_bytes(buf),
        Endian::Big => f32::from_be_bytes(buf),
    })
}

fn read_f64(file: &mut File, endian: Endian) -> TrajResult<f64> {
    let mut buf = [0u8; 8];
    file.read_exact(&mut buf)?;
    Ok(match endian {
        Endian::Little => f64::from_le_bytes(buf),
        Endian::Big => f64::from_be_bytes(buf),
    })
}

fn skip_record(file: &mut File, endian: Endian, marker_size: usize) -> TrajResult<()> {
    let len = read_marker(file, endian, marker_size)?;
    skip_record_with_len(file, endian, marker_size, len)
}

fn skip_record_with_len(
    file: &mut File,
    endian: Endian,
    marker_size: usize,
    len: u64,
) -> TrajResult<()> {
    file.seek(SeekFrom::Current(len as i64))?;
    let end_len = read_marker(file, endian, marker_size)?;
    if end_len != len {
        return Err(TrajError::Parse("record length mismatch".into()));
    }
    Ok(())
}

fn read_f32_record(
    file: &mut File,
    endian: Endian,
    marker_size: usize,
    count: usize,
) -> TrajResult<Vec<f32>> {
    let len = read_marker(file, endian, marker_size)?;
    read_f32_record_with_len(file, endian, marker_size, count, len)
}

fn read_f32_record_with_len(
    file: &mut File,
    endian: Endian,
    marker_size: usize,
    count: usize,
    len: u64,
) -> TrajResult<Vec<f32>> {
    let expected_len = (count * 4) as u64;
    if len != expected_len {
        return Err(TrajError::Parse("unexpected float record length".into()));
    }
    let mut values = Vec::with_capacity(count);
    for _ in 0..count {
        values.push(read_f32(file, endian)?);
    }
    let end_len = read_marker(file, endian, marker_size)?;
    if end_len != len {
        return Err(TrajError::Parse("float record length mismatch".into()));
    }
    Ok(values)
}

fn read_unitcell_with_len(
    file: &mut File,
    endian: Endian,
    marker_size: usize,
    len: u64,
    length_scale: f32,
) -> TrajResult<Box3> {
    let mut values = [0.0f64; 6];
    match len {
        24 => {
            for i in 0..6 {
                values[i] = read_f32(file, endian)? as f64;
            }
        }
        48 => {
            for i in 0..6 {
                values[i] = read_f64(file, endian)?;
            }
        }
        _ => {
            skip_record_with_len(file, endian, marker_size, len)?;
            return Ok(Box3::None);
        }
    }
    let end_len = read_marker(file, endian, marker_size)?;
    if end_len != len {
        return Err(TrajError::Parse("unitcell record length mismatch".into()));
    }

    let (mut a, mut b, mut c, alpha, beta, gamma) =
        (values[0], values[1], values[2], values[3], values[4], values[5]);
    a *= length_scale as f64;
    b *= length_scale as f64;
    c *= length_scale as f64;
    let (alpha_rad, beta_rad, gamma_rad) = if alpha.abs() <= 1.0 && beta.abs() <= 1.0 && gamma.abs() <= 1.0 {
        (alpha.acos(), beta.acos(), gamma.acos())
    } else {
        (
            alpha.to_radians(),
            beta.to_radians(),
            gamma.to_radians(),
        )
    };
    let ninety = std::f64::consts::FRAC_PI_2;
    let tol = 1e-3;
    if (alpha_rad - ninety).abs() < tol
        && (beta_rad - ninety).abs() < tol
        && (gamma_rad - ninety).abs() < tol
    {
        return Ok(Box3::Orthorhombic {
            lx: a as f32,
            ly: b as f32,
            lz: c as f32,
        });
    }

    let cos_alpha = alpha_rad.cos();
    let cos_beta = beta_rad.cos();
    let cos_gamma = gamma_rad.cos();
    let sin_gamma = gamma_rad.sin();
    if sin_gamma.abs() < 1e-8 {
        return Ok(Box3::None);
    }
    let ax = a;
    let ay = 0.0;
    let az = 0.0;
    let bx = b * cos_gamma;
    let by = b * sin_gamma;
    let bz = 0.0;
    let cx = c * cos_beta;
    let cy = c * (cos_alpha - cos_beta * cos_gamma) / sin_gamma;
    let cz_sq = c * c - cx * cx - cy * cy;
    let cz = if cz_sq > 0.0 { cz_sq.sqrt() } else { 0.0 };
    Ok(Box3::Triclinic {
        m: [
            ax as f32,
            ay as f32,
            az as f32,
            bx as f32,
            by as f32,
            bz as f32,
            cx as f32,
            cy as f32,
            cz as f32,
        ],
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn reject_invalid_header() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("bad.dcd");
        let mut file = File::create(&path).unwrap();
        file.write_all(&[1, 2, 3, 4]).unwrap();
        let err = DcdReader::open(&path, 1.0).unwrap_err();
        match err {
            TrajError::Unsupported(_) | TrajError::Io(_) | TrajError::Parse(_) => {}
            _ => panic!("unexpected error"),
        }
    }
}
