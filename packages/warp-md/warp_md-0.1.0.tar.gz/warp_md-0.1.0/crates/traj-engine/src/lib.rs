pub mod executor;
pub mod feature_store;
pub mod correlators;
pub mod plans;

pub use executor::{
    Device, DielectricOutput, Executor, GridOutput, PersistenceOutput, Plan, PlanOutput,
    RdfOutput, StructureFactorOutput,
};
pub use feature_store::{ChunkIndex, FeatureIndex, FeatureSchema, FeatureStoreReader, FeatureStoreWriter};
pub use correlators::{LagMode, LagSettings};
pub use plans::{
    BondAngleDistributionPlan, BondLengthDistributionPlan, ChainRgPlan, ContourLengthPlan,
    EndToEndPlan, PbcMode, PersistenceLengthPlan, RdfPlan, ReferenceMode, RgPlan, RmsdPlan,
};
pub use plans::analysis::{
    ConductivityPlan, DielectricPlan, DipoleAlignmentPlan, EquipartitionPlan, GroupBy, GroupMap,
    GroupSpec, HbondPlan, IonPairCorrelationPlan, MsdPlan, RotAcfPlan, StructureFactorPlan,
    WaterCountPlan,
};

#[cfg(test)]
mod tests {
    use super::*;
    use traj_core::error::TrajResult;
    use traj_core::frame::{Box3, FrameChunkBuilder};
    use traj_core::interner::StringInterner;
    use traj_core::system::{AtomTable, System};
    use traj_io::TrajReader;

    struct InMemoryTraj {
        n_atoms: usize,
        frames: Vec<Vec<[f32; 4]>>,
        cursor: usize,
    }

    impl InMemoryTraj {
        fn new(frames: Vec<Vec<[f32; 4]>>) -> Self {
            let n_atoms = frames.first().map(|f| f.len()).unwrap_or(0);
            Self {
                n_atoms,
                frames,
                cursor: 0,
            }
        }
    }

    impl TrajReader for InMemoryTraj {
        fn n_atoms(&self) -> usize {
            self.n_atoms
        }

        fn n_frames_hint(&self) -> Option<usize> {
            Some(self.frames.len())
        }

        fn read_chunk(&mut self, max_frames: usize, out: &mut FrameChunkBuilder) -> TrajResult<usize> {
            out.reset(self.n_atoms, max_frames);
            let mut count = 0;
            while self.cursor < self.frames.len() && count < max_frames {
                let coords = out.start_frame(Box3::None, None);
                coords.copy_from_slice(&self.frames[self.cursor]);
                self.cursor += 1;
                count += 1;
            }
            Ok(count)
        }
    }

    fn build_system() -> System {
        let mut interner = StringInterner::new();
        let name = interner.intern_upper("CA");
        let res = interner.intern_upper("ALA");
        let atoms = AtomTable {
            name_id: vec![name, name],
            resname_id: vec![res, res],
            resid: vec![1, 1],
            chain_id: vec![0, 0],
            element_id: vec![0, 0],
            mass: vec![1.0, 1.0],
        };
        let positions0 = Some(vec![[0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]]);
        System::with_atoms(atoms, interner, positions0)
    }

    fn build_two_resid_system() -> System {
        let mut interner = StringInterner::new();
        let name_a = interner.intern_upper("DA");
        let name_b = interner.intern_upper("AC");
        let res = interner.intern_upper("SOL");
        let atoms = AtomTable {
            name_id: vec![name_a, name_b],
            resname_id: vec![res, res],
            resid: vec![1, 2],
            chain_id: vec![0, 0],
            element_id: vec![0, 0],
            mass: vec![1.0, 1.0],
        };
        let positions0 = Some(vec![[0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]]);
        System::with_atoms(atoms, interner, positions0)
    }

    fn build_plane_system() -> System {
        let mut interner = StringInterner::new();
        let name = interner.intern_upper("CA");
        let res = interner.intern_upper("ALA");
        let atoms = AtomTable {
            name_id: vec![name, name, name],
            resname_id: vec![res, res, res],
            resid: vec![1, 1, 1],
            chain_id: vec![0, 0, 0],
            element_id: vec![0, 0, 0],
            mass: vec![1.0, 1.0, 1.0],
        };
        let positions0 = Some(vec![
            [0.0, 0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
        ]);
        System::with_atoms(atoms, interner, positions0)
    }

    fn build_polymer_system(n_chains: usize, chain_len: usize) -> System {
        let mut interner = StringInterner::new();
        let name = interner.intern_upper("C");
        let res = interner.intern_upper("POL");
        let n_atoms = n_chains * chain_len;
        let mut name_id = Vec::with_capacity(n_atoms);
        let mut resname_id = Vec::with_capacity(n_atoms);
        let mut resid = Vec::with_capacity(n_atoms);
        let mut chain_id = Vec::with_capacity(n_atoms);
        let mut element_id = Vec::with_capacity(n_atoms);
        let mut mass = Vec::with_capacity(n_atoms);
        let mut positions0 = Vec::with_capacity(n_atoms);
        for chain in 0..n_chains {
            for i in 0..chain_len {
                name_id.push(name);
                resname_id.push(res);
                resid.push((i + 1) as i32);
                chain_id.push(chain as u32);
                element_id.push(0);
                mass.push(1.0);
                positions0.push([0.0, 0.0, 0.0, 1.0]);
            }
        }
        let atoms = AtomTable {
            name_id,
            resname_id,
            resid,
            chain_id,
            element_id,
            mass,
        };
        System::with_atoms(atoms, interner, Some(positions0))
    }

    fn linear_frame(
        n_chains: usize,
        chain_len: usize,
        spacing: f32,
        y_sep: f32,
    ) -> Vec<[f32; 4]> {
        let mut coords = Vec::with_capacity(n_chains * chain_len);
        for chain in 0..n_chains {
            let y = chain as f32 * y_sep;
            for i in 0..chain_len {
                let x = i as f32 * spacing;
                coords.push([x, y, 0.0, 1.0]);
            }
        }
        coords
    }

    fn right_angle_frame(n_chains: usize, y_sep: f32) -> Vec<[f32; 4]> {
        let mut coords = Vec::with_capacity(n_chains * 3);
        for chain in 0..n_chains {
            let y = chain as f32 * y_sep;
            coords.push([0.0, y, 0.0, 1.0]);
            coords.push([1.0, y, 0.0, 1.0]);
            coords.push([1.0, y + 1.0, 0.0, 1.0]);
        }
        coords
    }

    #[test]
    fn rg_plan_basic() {
        let mut system = build_system();
        let sel = system.select("name CA").unwrap();
        let mut plan = RgPlan::new(sel, false);
        let frames = vec![
            vec![[0.0, 0.0, 0.0, 1.0], [2.0, 0.0, 0.0, 1.0]],
            vec![[1.0, 0.0, 0.0, 1.0], [3.0, 0.0, 0.0, 1.0]],
        ];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Series(vals) => {
                assert_eq!(vals.len(), 2);
                assert!((vals[0] - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn rmsd_plan_align_zero() {
        let mut system = build_system();
        let sel = system.select("name CA").unwrap();
        let mut plan = RmsdPlan::new(sel, ReferenceMode::Topology, true);
        let frames = vec![system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Series(vals) => {
                assert!((vals[0]).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn msd_plan_simple() {
        let mut system = build_system();
        let sel = system.select("name CA").unwrap();
        let mut plan = MsdPlan::new(sel, GroupBy::Resid);
        let frames = vec![
            vec![[0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]],
            vec![[1.0, 0.0, 0.0, 1.0], [2.0, 0.0, 0.0, 1.0]],
        ];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::TimeSeries { rows, cols, data, .. } => {
                assert_eq!(rows, 1);
                assert_eq!(cols, 8);
                assert!((data[0] - 1.0).abs() < 1e-6);
                assert!((data[1] - 1.0).abs() < 1e-6);
                assert!((data[6] - 1.0).abs() < 1e-6);
                assert!((data[7] - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn rotacf_plan_constant_orientation() {
        let mut system = build_plane_system();
        let sel = system.select("resid 1").unwrap();
        let orient = crate::plans::analysis::rotacf::OrientationSpec::PlaneIndices([1, 2, 3]);
        let mut plan = RotAcfPlan::new(sel, GroupBy::Resid, orient);
        let frames = vec![system.positions0.clone().unwrap(), system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::TimeSeries { data, cols, .. } => {
                assert_eq!(cols, 4);
                assert!((data[0] - 1.0).abs() < 1e-6);
                assert!((data[1] - 1.0).abs() < 1e-6);
                assert!((data[2] - 1.0).abs() < 1e-6);
                assert!((data[3] - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn ion_pair_corr_constant_pairs() {
        let mut system = build_two_resid_system();
        let sel = system.select("resid 1:2").unwrap();
        let group_types = vec![0usize, 1usize];
        let mut plan = IonPairCorrelationPlan::new(sel, GroupBy::Resid, 2.0, 2.0)
            .with_group_types(group_types);
        let frames = vec![system.positions0.clone().unwrap(), system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::TimeSeries { data, cols, rows, .. } => {
                assert_eq!(cols, 6);
                assert_eq!(rows, 2);
                assert!((data[0] - 1.0).abs() < 1e-6);
                assert!((data[3] - 1.0).abs() < 1e-6);
                assert!((data[6] - 1.0).abs() < 1e-6);
                assert!((data[9] - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn structure_factor_shapes() {
        let mut system = build_system();
        let sel = system.select("name CA").unwrap();
        let mut plan = StructureFactorPlan::new(sel, 5, 5.0, 4, 2.0, PbcMode::None);
        let frames = vec![system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::StructureFactor(output) => {
                assert_eq!(output.r.len(), 5);
                assert_eq!(output.g_r.len(), 5);
                assert_eq!(output.q.len(), 4);
                assert_eq!(output.s_q.len(), 4);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn water_count_basic() {
        let mut system = build_two_resid_system();
        let water = system.select("resid 1").unwrap();
        let center = system.select("resid 1").unwrap();
        let mut plan = WaterCountPlan::new(water, center, [0.5, 0.5, 0.5], [1.0, 1.0, 1.0]);
        let frames = vec![system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Grid(output) => {
                assert_eq!(output.dims, [3, 3, 3]);
                assert!((output.mean[0] - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn hbond_distance_only() {
        let mut system = build_two_resid_system();
        let donors = system.select("resid 1").unwrap();
        let acceptors = system.select("resid 2").unwrap();
        let mut plan = HbondPlan::new(donors, acceptors, 2.0);
        let frames = vec![system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::TimeSeries { data, cols, rows, .. } => {
                assert_eq!(cols, 1);
                assert_eq!(rows, 1);
                assert!((data[0] - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn rdf_plan_counts() {
        let mut system = build_system();
        let sel = system.select("name CA").unwrap();
        let mut plan = RdfPlan::new(sel.clone(), sel, 5, 5.0, PbcMode::None);
        let frames = vec![system.positions0.clone().unwrap()];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Rdf(rdf) => {
                let total: u64 = rdf.counts.iter().sum();
                assert!(total > 0);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn polymer_end_to_end_basic() {
        let mut system = build_polymer_system(2, 3);
        let sel = system.select("name C").unwrap();
        let mut plan = EndToEndPlan::new(sel);
        let frames = vec![linear_frame(2, 3, 1.0, 1.0)];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Matrix { data, rows, cols } => {
                assert_eq!(rows, 1);
                assert_eq!(cols, 2);
                assert_eq!(data.len(), 2);
                assert!((data[0] - 2.0).abs() < 1e-6);
                assert!((data[1] - 2.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn polymer_contour_length_basic() {
        let mut system = build_polymer_system(2, 3);
        let sel = system.select("name C").unwrap();
        let mut plan = ContourLengthPlan::new(sel);
        let frames = vec![linear_frame(2, 3, 1.0, 1.0)];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Matrix { data, rows, cols } => {
                assert_eq!(rows, 1);
                assert_eq!(cols, 2);
                assert_eq!(data.len(), 2);
                assert!((data[0] - 2.0).abs() < 1e-6);
                assert!((data[1] - 2.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn polymer_chain_rg_basic() {
        let mut system = build_polymer_system(2, 3);
        let sel = system.select("name C").unwrap();
        let mut plan = ChainRgPlan::new(sel);
        let frames = vec![linear_frame(2, 3, 1.0, 1.0)];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Matrix { data, rows, cols } => {
                let expected = (2.0f32 / 3.0f32).sqrt();
                assert_eq!(rows, 1);
                assert_eq!(cols, 2);
                assert!((data[0] - expected).abs() < 1e-6);
                assert!((data[1] - expected).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn polymer_bond_length_histogram() {
        let mut system = build_polymer_system(2, 3);
        let sel = system.select("name C").unwrap();
        let mut plan = BondLengthDistributionPlan::new(sel, 2, 2.0);
        let frames = vec![linear_frame(2, 3, 1.0, 1.0)];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Histogram { centers: _, counts } => {
                assert_eq!(counts.len(), 2);
                assert_eq!(counts[0], 0);
                assert_eq!(counts[1], 4);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn polymer_bond_angle_histogram() {
        let mut system = build_polymer_system(2, 3);
        let sel = system.select("name C").unwrap();
        let mut plan = BondAngleDistributionPlan::new(sel, 3, true);
        let frames = vec![right_angle_frame(2, 1.0)];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Histogram { centers: _, counts } => {
                assert_eq!(counts.len(), 3);
                assert_eq!(counts[1], 2);
            }
            _ => panic!("unexpected output"),
        }
    }

    #[test]
    fn polymer_persistence_basic() {
        let mut system = build_polymer_system(1, 3);
        let sel = system.select("name C").unwrap();
        let mut plan = PersistenceLengthPlan::new(sel);
        let frames = vec![linear_frame(1, 3, 1.0, 0.0)];
        let mut traj = InMemoryTraj::new(frames);
        let mut exec = Executor::new(system);
        let out = exec.run_plan(&mut plan, &mut traj).unwrap();
        match out {
            PlanOutput::Persistence(p) => {
                assert_eq!(p.bond_autocorrelation.len(), 2);
                assert!((p.bond_autocorrelation[0] - 1.0).abs() < 1e-6);
                assert!((p.lb - 1.0).abs() < 1e-6);
            }
            _ => panic!("unexpected output"),
        }
    }
}
