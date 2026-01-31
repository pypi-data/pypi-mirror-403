use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;

use traj_core::elements::{infer_element_from_atom_name, mass_for_element};
use traj_core::error::{TrajError, TrajResult};
use traj_core::system::{AtomTable, System};

use crate::TopologyReader;

pub struct GroReader {
    path: PathBuf,
}

impl GroReader {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self { path: path.into() }
    }
}

impl TopologyReader for GroReader {
    fn read_system(&mut self) -> TrajResult<System> {
        let file = File::open(&self.path)?;
        let mut reader = BufReader::new(file);
        let mut line = String::new();

        line.clear();
        reader.read_line(&mut line)?;
        line.clear();
        reader.read_line(&mut line)?;
        let n_atoms: usize = line.trim().parse().map_err(|_| {
            TrajError::Parse(format!("invalid atom count '{}'", line.trim()))
        })?;

        let mut system = System::new();
        let mut positions = Vec::with_capacity(n_atoms);
        let mut atoms = AtomTable::default();

        for _ in 0..n_atoms {
            line.clear();
            reader.read_line(&mut line)?;
            if line.len() < 44 {
                return Err(TrajError::Parse("GRO atom line too short".into()));
            }
            let resid_str = line.get(0..5).unwrap_or(" ").trim();
            let resname = line.get(5..10).unwrap_or(" ").trim();
            let atomname = line.get(10..15).unwrap_or(" ").trim();
            let _atomnr = line.get(15..20).unwrap_or(" ").trim();
            let x_str = line.get(20..28).unwrap_or(" ").trim();
            let y_str = line.get(28..36).unwrap_or(" ").trim();
            let z_str = line.get(36..44).unwrap_or(" ").trim();

            let resid: i32 = resid_str.parse().map_err(|_| {
                TrajError::Parse(format!("invalid resid '{resid_str}'"))
            })?;
            let x_nm: f32 = x_str.parse().map_err(|_| {
                TrajError::Parse(format!("invalid x coord '{x_str}'"))
            })?;
            let y_nm: f32 = y_str.parse().map_err(|_| {
                TrajError::Parse(format!("invalid y coord '{y_str}'"))
            })?;
            let z_nm: f32 = z_str.parse().map_err(|_| {
                TrajError::Parse(format!("invalid z coord '{z_str}'"))
            })?;

            let name_id = system.interner.intern_upper(atomname);
            let resname_id = system.interner.intern_upper(resname);
            let chain_id = system.interner.intern_upper("");

            let element = infer_element_from_atom_name(atomname).unwrap_or_else(|| "".to_string());
            let element_id = system.interner.intern_upper(&element);
            let mass = if element.is_empty() { 0.0 } else { mass_for_element(&element) };

            atoms.name_id.push(name_id);
            atoms.resname_id.push(resname_id);
            atoms.resid.push(resid);
            atoms.chain_id.push(chain_id);
            atoms.element_id.push(element_id);
            atoms.mass.push(mass);
            positions.push([x_nm * 10.0, y_nm * 10.0, z_nm * 10.0, 1.0]);
        }

        system.atoms = atoms;
        system.positions0 = Some(positions);
        system.validate_positions0()?;
        Ok(system)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn read_simple_gro() {
        let content = "Test\n   2\n    1ALA      N    1   0.000   0.000   0.000\n    1ALA     CA    2   0.100   0.000   0.000\n   1.0 1.0 1.0\n";
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("test.gro");
        let mut file = File::create(&path).unwrap();
        file.write_all(content.as_bytes()).unwrap();
        let mut reader = GroReader::new(&path);
        let system = reader.read_system().unwrap();
        assert_eq!(system.n_atoms(), 2);
        let pos = system.positions0.unwrap();
        assert!((pos[1][0] - 1.0).abs() < 1e-6);
    }
}
