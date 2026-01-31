use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;

use traj_core::elements::{infer_element_from_atom_name, mass_for_element, normalize_element};
use traj_core::error::{TrajError, TrajResult};
use traj_core::system::{AtomTable, System};

use crate::TopologyReader;

pub struct PdbReader {
    path: PathBuf,
}

impl PdbReader {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self { path: path.into() }
    }
}

impl TopologyReader for PdbReader {
    fn read_system(&mut self) -> TrajResult<System> {
        let file = File::open(&self.path)?;
        let reader = BufReader::new(file);
        let mut system = System::new();
        let mut positions = Vec::new();
        let mut atoms = AtomTable::default();
        let mut in_model = false;
        let mut saw_model = false;

        for line in reader.lines() {
            let line = line?;
            if line.starts_with("MODEL") {
                if saw_model {
                    break;
                }
                saw_model = true;
                in_model = true;
                continue;
            }
            if line.starts_with("ENDMDL") {
                if saw_model {
                    break;
                }
                continue;
            }
            if line.starts_with("ATOM") || line.starts_with("HETATM") {
                if saw_model && !in_model {
                    continue;
                }
                let alt_loc = line.chars().nth(16).unwrap_or(' ');
                if alt_loc != ' ' && alt_loc != 'A' {
                    continue;
                }
                let name = slice_trim(&line, 12, 16)?;
                let resname = slice_trim(&line, 17, 20)?;
                let chain = slice_trim(&line, 21, 22)?;
                let resid_str = slice_trim(&line, 22, 26)?;
                let x_str = slice_trim(&line, 30, 38)?;
                let y_str = slice_trim(&line, 38, 46)?;
                let z_str = slice_trim(&line, 46, 54)?;
                let element_str = slice_trim(&line, 76, 78).ok();

                let resid: i32 = resid_str.trim().parse().map_err(|_| {
                    TrajError::Parse(format!("invalid resid '{resid_str}'"))
                })?;
                let x: f32 = x_str.trim().parse().map_err(|_| {
                    TrajError::Parse(format!("invalid x coord '{x_str}'"))
                })?;
                let y: f32 = y_str.trim().parse().map_err(|_| {
                    TrajError::Parse(format!("invalid y coord '{y_str}'"))
                })?;
                let z: f32 = z_str.trim().parse().map_err(|_| {
                    TrajError::Parse(format!("invalid z coord '{z_str}'"))
                })?;

                let name_id = system.interner.intern_upper(name.trim());
                let resname_id = system.interner.intern_upper(resname.trim());
                let chain_id = system.interner.intern_upper(chain.trim());

                let element = element_str
                    .and_then(|s| normalize_element(s))
                    .or_else(|| infer_element_from_atom_name(name.trim()))
                    .unwrap_or_else(|| "".to_string());
                let element_id = system.interner.intern_upper(&element);
                let mass = if element.is_empty() { 0.0 } else { mass_for_element(&element) };

                atoms.name_id.push(name_id);
                atoms.resname_id.push(resname_id);
                atoms.resid.push(resid);
                atoms.chain_id.push(chain_id);
                atoms.element_id.push(element_id);
                atoms.mass.push(mass);
                positions.push([x, y, z, 1.0]);
            }
        }

        if atoms.is_empty() {
            return Err(TrajError::Parse("no atoms found in PDB".into()));
        }

        system.atoms = atoms;
        system.positions0 = Some(positions);
        system.validate_positions0()?;
        Ok(system)
    }
}

fn slice_trim(line: &str, start: usize, end: usize) -> TrajResult<&str> {
    line.get(start..end)
        .map(|s| s.trim())
        .ok_or_else(|| TrajError::Parse("line too short".into()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn read_simple_pdb() {
        let content = "ATOM      1  N   ALA A   1      11.104  13.207  14.099  1.00 20.00           N\n\
ATOM      2  CA  ALA A   1      12.560  13.207  14.099  1.00 20.00           C\n\
TER\n";
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("test.pdb");
        let mut file = File::create(&path).unwrap();
        file.write_all(content.as_bytes()).unwrap();
        let mut reader = PdbReader::new(&path);
        let system = reader.read_system().unwrap();
        assert_eq!(system.n_atoms(), 2);
        let pos = system.positions0.unwrap();
        assert_eq!(pos.len(), 2);
        assert!((pos[0][0] - 11.104).abs() < 1e-3);
    }
}
