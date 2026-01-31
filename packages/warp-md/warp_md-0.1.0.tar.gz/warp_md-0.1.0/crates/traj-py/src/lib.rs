use std::cell::RefCell;

use numpy::ndarray::Array2;
use numpy::{IntoPyArray, PyArray1, PyArray2};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use traj_core::error::TrajError;
use traj_core::selection::Selection;
use traj_core::system::System;
use traj_engine::{
    BondAngleDistributionPlan, BondLengthDistributionPlan, ChainRgPlan, ConductivityPlan,
    ContourLengthPlan, DielectricPlan, DipoleAlignmentPlan, EndToEndPlan, EquipartitionPlan,
    Executor, GroupBy, HbondPlan, IonPairCorrelationPlan, LagMode, MsdPlan, PbcMode,
    PersistenceLengthPlan, Plan, PlanOutput, RdfPlan, ReferenceMode, RgPlan, RmsdPlan,
    RotAcfPlan, StructureFactorPlan, WaterCountPlan,
};
use traj_io::dcd::DcdReader;
use traj_io::gro::GroReader;
use traj_io::pdb::PdbReader;
use traj_io::xtc::XtcReader;
use traj_io::{TopologyReader, TrajReader};
use traj_engine::plans::analysis::msd::{DtDecimation, FrameDecimation, TimeBinning};
use traj_engine::plans::analysis::rotacf::OrientationSpec;

#[pyclass]
struct PySystem {
    system: RefCell<System>,
}

#[pymethods]
impl PySystem {
    #[staticmethod]
    fn from_pdb(path: &str) -> PyResult<Self> {
        let mut reader = PdbReader::new(path);
        let system = reader.read_system().map_err(to_py_err)?;
        Ok(Self {
            system: RefCell::new(system),
        })
    }

    #[staticmethod]
    fn from_gro(path: &str) -> PyResult<Self> {
        let mut reader = GroReader::new(path);
        let system = reader.read_system().map_err(to_py_err)?;
        Ok(Self {
            system: RefCell::new(system),
        })
    }

    fn select(&self, expr: &str) -> PyResult<PySelection> {
        let mut sys = self.system.borrow_mut();
        let selection = sys.select(expr).map_err(to_py_err)?;
        Ok(PySelection { selection })
    }

    fn n_atoms(&self) -> PyResult<usize> {
        Ok(self.system.borrow().n_atoms())
    }

    fn atom_table<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        let sys = self.system.borrow();
        let atoms = &sys.atoms;
        let mut names = Vec::with_capacity(atoms.name_id.len());
        let mut resnames = Vec::with_capacity(atoms.resname_id.len());
        for &id in atoms.name_id.iter() {
            names.push(sys.interner.resolve(id).unwrap_or("").to_string());
        }
        for &id in atoms.resname_id.iter() {
            resnames.push(sys.interner.resolve(id).unwrap_or("").to_string());
        }
        let dict = PyDict::new(py);
        dict.set_item("name", names)?;
        dict.set_item("resname", resnames)?;
        dict.set_item("resid", atoms.resid.clone())?;
        dict.set_item("chain_id", atoms.chain_id.clone())?;
        dict.set_item("mass", atoms.mass.clone())?;
        Ok(dict.into_py(py))
    }
}

#[pyclass]
struct PySelection {
    selection: Selection,
}

#[pymethods]
impl PySelection {
    #[getter]
    fn indices<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        let vec: Vec<u32> = self.selection.indices.as_ref().clone();
        Ok(vec.into_py(py))
    }
}

enum TrajKind {
    Dcd(DcdReader),
    Xtc(XtcReader),
}

#[pyclass(unsendable)]
struct PyTrajectory {
    inner: RefCell<TrajKind>,
}

#[pymethods]
impl PyTrajectory {
    #[staticmethod]
    #[pyo3(signature = (path, system, length_scale=None))]
    fn open_dcd(path: &str, system: &PySystem, length_scale: Option<f32>) -> PyResult<Self> {
        let reader = DcdReader::open(path, length_scale.unwrap_or(1.0)).map_err(to_py_err)?;
        let sys = system.system.borrow();
        if reader.n_atoms() != sys.n_atoms() {
            return Err(PyRuntimeError::new_err(
                "trajectory atom count does not match system",
            ));
        }
        Ok(Self {
            inner: RefCell::new(TrajKind::Dcd(reader)),
        })
    }

    #[staticmethod]
    fn open_xtc(path: &str, system: &PySystem) -> PyResult<Self> {
        let reader = XtcReader::open(path).map_err(to_py_err)?;
        let sys = system.system.borrow();
        if reader.n_atoms() != sys.n_atoms() {
            return Err(PyRuntimeError::new_err(
                "trajectory atom count does not match system",
            ));
        }
        Ok(Self {
            inner: RefCell::new(TrajKind::Xtc(reader)),
        })
    }

    fn n_atoms(&self) -> PyResult<usize> {
        let inner = self.inner.borrow();
        let n = match &*inner {
            TrajKind::Dcd(reader) => reader.n_atoms(),
            TrajKind::Xtc(reader) => reader.n_atoms(),
        };
        Ok(n)
    }
}

#[pyclass]
struct PyRgPlan {
    plan: RefCell<RgPlan>,
}

#[pymethods]
impl PyRgPlan {
    #[new]
    fn new(selection: &PySelection, mass_weighted: Option<bool>) -> Self {
        let plan = RgPlan::new(selection.selection.clone(), mass_weighted.unwrap_or(false));
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<&'py PyArray1<f32>> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Series(values) => Ok(PyArray1::from_vec(py, values)),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyRmsdPlan {
    plan: RefCell<RmsdPlan>,
}

#[pymethods]
impl PyRmsdPlan {
    #[new]
    #[pyo3(signature = (selection, reference="topology", align=true))]
    fn new(selection: &PySelection, reference: &str, align: bool) -> PyResult<Self> {
        let reference_mode = parse_reference(reference)?;
        let plan = RmsdPlan::new(selection.selection.clone(), reference_mode, align);
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<&'py PyArray1<f32>> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Series(values) => Ok(PyArray1::from_vec(py, values)),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyMsdPlan {
    plan: RefCell<MsdPlan>,
}

#[pymethods]
impl PyMsdPlan {
    #[new]
    #[pyo3(signature = (selection, group_by="resid", axis=None, length_scale=None, frame_decimation=None, dt_decimation=None, time_binning=None, group_types=None, lag_mode=None, max_lag=None, memory_budget_bytes=None, multi_tau_m=None, multi_tau_levels=None))]
    fn new(
        selection: &PySelection,
        group_by: &str,
        axis: Option<(f64, f64, f64)>,
        length_scale: Option<f64>,
        frame_decimation: Option<(usize, usize)>,
        dt_decimation: Option<(usize, usize, usize, usize)>,
        time_binning: Option<(f64, f64)>,
        group_types: Option<Vec<usize>>,
        lag_mode: Option<&str>,
        max_lag: Option<usize>,
        memory_budget_bytes: Option<usize>,
        multi_tau_m: Option<usize>,
        multi_tau_levels: Option<usize>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let mut plan = MsdPlan::new(selection.selection.clone(), group_by);
        if let Some(axis) = axis {
            plan = plan.with_axis([axis.0, axis.1, axis.2]);
        }
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some((start, stride)) = frame_decimation {
            plan = plan.with_frame_decimation(FrameDecimation { start, stride });
        }
        if let Some((cut1, stride1, cut2, stride2)) = dt_decimation {
            plan = plan.with_dt_decimation(DtDecimation {
                cut1,
                stride1,
                cut2,
                stride2,
            });
        }
        if let Some((eps_num, eps_add)) = time_binning {
            plan = plan.with_time_binning(TimeBinning { eps_num, eps_add });
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        if let Some(mode) = lag_mode {
            plan = plan.with_lag_mode(parse_lag_mode(mode)?);
        }
        if let Some(max_lag) = max_lag {
            plan = plan.with_max_lag(max_lag);
        }
        if let Some(budget) = memory_budget_bytes {
            plan = plan.with_memory_budget_bytes(budget);
        }
        if let Some(m) = multi_tau_m {
            plan = plan.with_multi_tau_m(m);
        }
        if let Some(levels) = multi_tau_levels {
            plan = plan.with_multi_tau_levels(levels);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyRotAcfPlan {
    plan: RefCell<RotAcfPlan>,
}

#[pymethods]
impl PyRotAcfPlan {
    #[new]
    #[pyo3(signature = (selection, group_by="resid", orientation=None, p2_legendre=true, length_scale=None, frame_decimation=None, dt_decimation=None, time_binning=None, group_types=None, lag_mode=None, max_lag=None, memory_budget_bytes=None, multi_tau_m=None, multi_tau_levels=None))]
    fn new(
        selection: &PySelection,
        group_by: &str,
        orientation: Option<Vec<usize>>,
        p2_legendre: bool,
        length_scale: Option<f64>,
        frame_decimation: Option<(usize, usize)>,
        dt_decimation: Option<(usize, usize, usize, usize)>,
        time_binning: Option<(f64, f64)>,
        group_types: Option<Vec<usize>>,
        lag_mode: Option<&str>,
        max_lag: Option<usize>,
        memory_budget_bytes: Option<usize>,
        multi_tau_m: Option<usize>,
        multi_tau_levels: Option<usize>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let orient = match orientation {
            Some(ref v) if v.len() == 2 => {
                OrientationSpec::VectorIndices([v[0], v[1]])
            }
            Some(ref v) if v.len() == 3 => {
                OrientationSpec::PlaneIndices([v[0], v[1], v[2]])
            }
            Some(_) => {
                return Err(PyRuntimeError::new_err(
                    "orientation must be length-2 (vector) or length-3 (plane) indices",
                ))
            }
            None => {
                return Err(PyRuntimeError::new_err(
                    "orientation indices required for rotacf plan",
                ))
            }
        };
        let mut plan = RotAcfPlan::new(selection.selection.clone(), group_by, orient)
            .with_p2_legendre(p2_legendre);
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some((start, stride)) = frame_decimation {
            plan = plan.with_frame_decimation(FrameDecimation { start, stride });
        }
        if let Some((cut1, stride1, cut2, stride2)) = dt_decimation {
            plan = plan.with_dt_decimation(DtDecimation {
                cut1,
                stride1,
                cut2,
                stride2,
            });
        }
        if let Some((eps_num, eps_add)) = time_binning {
            plan = plan.with_time_binning(TimeBinning { eps_num, eps_add });
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        if let Some(mode) = lag_mode {
            plan = plan.with_lag_mode(parse_lag_mode(mode)?);
        }
        if let Some(max_lag) = max_lag {
            plan = plan.with_max_lag(max_lag);
        }
        if let Some(budget) = memory_budget_bytes {
            plan = plan.with_memory_budget_bytes(budget);
        }
        if let Some(m) = multi_tau_m {
            plan = plan.with_multi_tau_m(m);
        }
        if let Some(levels) = multi_tau_levels {
            plan = plan.with_multi_tau_levels(levels);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyConductivityPlan {
    plan: RefCell<ConductivityPlan>,
}

#[pymethods]
impl PyConductivityPlan {
    #[new]
    #[pyo3(signature = (selection, charges, temperature, group_by="resid", transference=false, length_scale=None, frame_decimation=None, dt_decimation=None, time_binning=None, group_types=None, lag_mode=None, max_lag=None, memory_budget_bytes=None, multi_tau_m=None, multi_tau_levels=None))]
    fn new(
        selection: &PySelection,
        charges: Vec<f64>,
        temperature: f64,
        group_by: &str,
        transference: bool,
        length_scale: Option<f64>,
        frame_decimation: Option<(usize, usize)>,
        dt_decimation: Option<(usize, usize, usize, usize)>,
        time_binning: Option<(f64, f64)>,
        group_types: Option<Vec<usize>>,
        lag_mode: Option<&str>,
        max_lag: Option<usize>,
        memory_budget_bytes: Option<usize>,
        multi_tau_m: Option<usize>,
        multi_tau_levels: Option<usize>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let mut plan = ConductivityPlan::new(selection.selection.clone(), group_by, charges, temperature)
            .with_transference(transference);
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some((start, stride)) = frame_decimation {
            plan = plan.with_frame_decimation(FrameDecimation { start, stride });
        }
        if let Some((cut1, stride1, cut2, stride2)) = dt_decimation {
            plan = plan.with_dt_decimation(DtDecimation {
                cut1,
                stride1,
                cut2,
                stride2,
            });
        }
        if let Some((eps_num, eps_add)) = time_binning {
            plan = plan.with_time_binning(TimeBinning { eps_num, eps_add });
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        if let Some(mode) = lag_mode {
            plan = plan.with_lag_mode(parse_lag_mode(mode)?);
        }
        if let Some(max_lag) = max_lag {
            plan = plan.with_max_lag(max_lag);
        }
        if let Some(budget) = memory_budget_bytes {
            plan = plan.with_memory_budget_bytes(budget);
        }
        if let Some(m) = multi_tau_m {
            plan = plan.with_multi_tau_m(m);
        }
        if let Some(levels) = multi_tau_levels {
            plan = plan.with_multi_tau_levels(levels);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyDielectricPlan {
    plan: RefCell<DielectricPlan>,
}

#[pymethods]
impl PyDielectricPlan {
    #[new]
    #[pyo3(signature = (selection, charges, group_by="resid", length_scale=None, group_types=None))]
    fn new(
        selection: &PySelection,
        charges: Vec<f64>,
        group_by: &str,
        length_scale: Option<f64>,
        group_types: Option<Vec<usize>>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let mut plan = DielectricPlan::new(selection.selection.clone(), group_by, charges);
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Dielectric(output) => dielectric_to_py(py, output),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyDipoleAlignmentPlan {
    plan: RefCell<DipoleAlignmentPlan>,
}

#[pymethods]
impl PyDipoleAlignmentPlan {
    #[new]
    #[pyo3(signature = (selection, charges, group_by="resid", length_scale=None, group_types=None))]
    fn new(
        selection: &PySelection,
        charges: Vec<f64>,
        group_by: &str,
        length_scale: Option<f64>,
        group_types: Option<Vec<usize>>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let mut plan = DipoleAlignmentPlan::new(selection.selection.clone(), group_by, charges);
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyIonPairCorrelationPlan {
    plan: RefCell<IonPairCorrelationPlan>,
}

#[pymethods]
impl PyIonPairCorrelationPlan {
    #[new]
    #[pyo3(signature = (selection, rclust_cat, rclust_ani, group_by="resid", cation_type=0, anion_type=1, max_cluster=10, length_scale=None, group_types=None, lag_mode=None, max_lag=None, memory_budget_bytes=None, multi_tau_m=None, multi_tau_levels=None))]
    fn new(
        selection: &PySelection,
        rclust_cat: f64,
        rclust_ani: f64,
        group_by: &str,
        cation_type: usize,
        anion_type: usize,
        max_cluster: usize,
        length_scale: Option<f64>,
        group_types: Option<Vec<usize>>,
        lag_mode: Option<&str>,
        max_lag: Option<usize>,
        memory_budget_bytes: Option<usize>,
        multi_tau_m: Option<usize>,
        multi_tau_levels: Option<usize>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let mut plan =
            IonPairCorrelationPlan::new(selection.selection.clone(), group_by, rclust_cat, rclust_ani)
                .with_types(cation_type, anion_type)
                .with_max_cluster(max_cluster);
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        if let Some(mode) = lag_mode {
            plan = plan.with_lag_mode(parse_lag_mode(mode)?);
        }
        if let Some(max_lag) = max_lag {
            plan = plan.with_max_lag(max_lag);
        }
        if let Some(budget) = memory_budget_bytes {
            plan = plan.with_memory_budget_bytes(budget);
        }
        if let Some(m) = multi_tau_m {
            plan = plan.with_multi_tau_m(m);
        }
        if let Some(levels) = multi_tau_levels {
            plan = plan.with_multi_tau_levels(levels);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyStructureFactorPlan {
    plan: RefCell<StructureFactorPlan>,
}

#[pymethods]
impl PyStructureFactorPlan {
    #[new]
    #[pyo3(signature = (selection, bins, r_max, q_bins, q_max, pbc="orthorhombic", length_scale=None))]
    fn new(
        selection: &PySelection,
        bins: usize,
        r_max: f64,
        q_bins: usize,
        q_max: f64,
        pbc: &str,
        length_scale: Option<f64>,
    ) -> PyResult<Self> {
        let pbc = parse_pbc(pbc)?;
        let mut plan = StructureFactorPlan::new(selection.selection.clone(), bins, r_max, q_bins, q_max, pbc);
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::StructureFactor(output) => structure_factor_to_py(py, output),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyWaterCountPlan {
    plan: RefCell<WaterCountPlan>,
}

#[pymethods]
impl PyWaterCountPlan {
    #[new]
    #[pyo3(signature = (water_selection, center_selection, box_unit, region_size, shift=None, length_scale=None))]
    fn new(
        water_selection: &PySelection,
        center_selection: &PySelection,
        box_unit: (f64, f64, f64),
        region_size: (f64, f64, f64),
        shift: Option<(f64, f64, f64)>,
        length_scale: Option<f64>,
    ) -> PyResult<Self> {
        let mut plan = WaterCountPlan::new(
            water_selection.selection.clone(),
            center_selection.selection.clone(),
            [box_unit.0, box_unit.1, box_unit.2],
            [region_size.0, region_size.1, region_size.2],
        );
        if let Some(shift) = shift {
            plan = plan.with_shift([shift.0, shift.1, shift.2]);
        }
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Grid(output) => grid_to_py(py, output),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyEquipartitionPlan {
    plan: RefCell<EquipartitionPlan>,
}

#[pymethods]
impl PyEquipartitionPlan {
    #[new]
    #[pyo3(signature = (selection, group_by="resid", velocity_scale=None, length_scale=None, group_types=None))]
    fn new(
        selection: &PySelection,
        group_by: &str,
        velocity_scale: Option<f64>,
        length_scale: Option<f64>,
        group_types: Option<Vec<usize>>,
    ) -> PyResult<Self> {
        let group_by = parse_group_by(group_by)?;
        let mut plan = EquipartitionPlan::new(selection.selection.clone(), group_by);
        if let Some(scale) = velocity_scale {
            plan = plan.with_velocity_scale(scale);
        }
        if let Some(scale) = length_scale {
            plan = plan.with_length_scale(scale);
        }
        if let Some(types) = group_types {
            plan = plan.with_group_types(types);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyHbondPlan {
    plan: RefCell<HbondPlan>,
}

#[pymethods]
impl PyHbondPlan {
    #[new]
    #[pyo3(signature = (donors, acceptors, dist_cutoff, hydrogens=None, angle_cutoff=None))]
    fn new(
        donors: &PySelection,
        acceptors: &PySelection,
        dist_cutoff: f64,
        hydrogens: Option<&PySelection>,
        angle_cutoff: Option<f64>,
    ) -> PyResult<Self> {
        let mut plan = HbondPlan::new(donors.selection.clone(), acceptors.selection.clone(), dist_cutoff);
        if let Some(h_sel) = hydrogens {
            let cutoff = angle_cutoff.ok_or_else(|| {
                PyRuntimeError::new_err("angle_cutoff required when hydrogens are provided")
            })?;
            plan = plan.with_hydrogens(h_sel.selection.clone(), cutoff);
        }
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::TimeSeries { time, data, rows, cols } => {
                timeseries_to_py(py, time, data, rows, cols)
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyRdfPlan {
    plan: RefCell<RdfPlan>,
}

#[pymethods]
impl PyRdfPlan {
    #[new]
    #[pyo3(signature = (sel_a, sel_b, bins, r_max, pbc="orthorhombic"))]
    fn new(sel_a: &PySelection, sel_b: &PySelection, bins: usize, r_max: f32, pbc: &str) -> PyResult<Self> {
        let pbc = parse_pbc(pbc)?;
        let plan = RdfPlan::new(sel_a.selection.clone(), sel_b.selection.clone(), bins, r_max, pbc);
        Ok(Self {
            plan: RefCell::new(plan),
        })
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Rdf(rdf) => {
                let r = PyArray1::from_vec(py, rdf.r);
                let g = PyArray1::from_vec(py, rdf.g_r);
                let counts = PyArray1::from_vec(py, rdf.counts);
                Ok((r, g, counts).into_py(py))
            }
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyEndToEndPlan {
    plan: RefCell<EndToEndPlan>,
}

#[pymethods]
impl PyEndToEndPlan {
    #[new]
    fn new(selection: &PySelection) -> Self {
        let plan = EndToEndPlan::new(selection.selection.clone());
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<&'py PyArray2<f32>> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Matrix { data, rows, cols } => matrix_to_py(py, data, rows, cols),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyContourLengthPlan {
    plan: RefCell<ContourLengthPlan>,
}

#[pymethods]
impl PyContourLengthPlan {
    #[new]
    fn new(selection: &PySelection) -> Self {
        let plan = ContourLengthPlan::new(selection.selection.clone());
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<&'py PyArray2<f32>> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Matrix { data, rows, cols } => matrix_to_py(py, data, rows, cols),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyChainRgPlan {
    plan: RefCell<ChainRgPlan>,
}

#[pymethods]
impl PyChainRgPlan {
    #[new]
    fn new(selection: &PySelection) -> Self {
        let plan = ChainRgPlan::new(selection.selection.clone());
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<&'py PyArray2<f32>> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Matrix { data, rows, cols } => matrix_to_py(py, data, rows, cols),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyBondLengthDistributionPlan {
    plan: RefCell<BondLengthDistributionPlan>,
}

#[pymethods]
impl PyBondLengthDistributionPlan {
    #[new]
    fn new(selection: &PySelection, bins: usize, r_max: f32) -> Self {
        let plan = BondLengthDistributionPlan::new(selection.selection.clone(), bins, r_max);
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Histogram { centers, counts } => Ok(hist_to_py(py, centers, counts)),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyBondAngleDistributionPlan {
    plan: RefCell<BondAngleDistributionPlan>,
}

#[pymethods]
impl PyBondAngleDistributionPlan {
    #[new]
    #[pyo3(signature = (selection, bins, degrees=true))]
    fn new(selection: &PySelection, bins: usize, degrees: bool) -> Self {
        let plan = BondAngleDistributionPlan::new(selection.selection.clone(), bins, degrees);
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Histogram { centers, counts } => Ok(hist_to_py(py, centers, counts)),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pyclass]
struct PyPersistenceLengthPlan {
    plan: RefCell<PersistenceLengthPlan>,
}

#[pymethods]
impl PyPersistenceLengthPlan {
    #[new]
    fn new(selection: &PySelection) -> Self {
        let plan = PersistenceLengthPlan::new(selection.selection.clone());
        Self {
            plan: RefCell::new(plan),
        }
    }

    #[pyo3(signature = (traj, system, chunk_frames=None, device="auto"))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        traj: &PyTrajectory,
        system: &PySystem,
        chunk_frames: Option<usize>,
        device: &str,
    ) -> PyResult<PyObject> {
        let mut plan = self.plan.borrow_mut();
        let mut traj_ref = traj.inner.borrow_mut();
        let output = run_plan(&mut *plan, &mut traj_ref, &system.system.borrow(), chunk_frames, device)?;
        match output {
            PlanOutput::Persistence(p) => persistence_to_py(py, p),
            _ => Err(PyRuntimeError::new_err("unexpected output")),
        }
    }
}

#[pymodule]
fn traj_py(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<PySystem>()?;
    m.add_class::<PySelection>()?;
    m.add_class::<PyTrajectory>()?;
    m.add_class::<PyRgPlan>()?;
    m.add_class::<PyRmsdPlan>()?;
    m.add_class::<PyMsdPlan>()?;
    m.add_class::<PyRotAcfPlan>()?;
    m.add_class::<PyConductivityPlan>()?;
    m.add_class::<PyDielectricPlan>()?;
    m.add_class::<PyDipoleAlignmentPlan>()?;
    m.add_class::<PyIonPairCorrelationPlan>()?;
    m.add_class::<PyStructureFactorPlan>()?;
    m.add_class::<PyWaterCountPlan>()?;
    m.add_class::<PyEquipartitionPlan>()?;
    m.add_class::<PyHbondPlan>()?;
    m.add_class::<PyRdfPlan>()?;
    m.add_class::<PyEndToEndPlan>()?;
    m.add_class::<PyContourLengthPlan>()?;
    m.add_class::<PyChainRgPlan>()?;
    m.add_class::<PyBondLengthDistributionPlan>()?;
    m.add_class::<PyBondAngleDistributionPlan>()?;
    m.add_class::<PyPersistenceLengthPlan>()?;
    Ok(())
}

fn to_py_err(err: TrajError) -> PyErr {
    PyRuntimeError::new_err(err.to_string())
}

fn run_plan<P: Plan>(
    plan: &mut P,
    traj: &mut TrajKind,
    system: &System,
    chunk_frames: Option<usize>,
    device: &str,
) -> PyResult<PlanOutput> {
    let mut exec = Executor::new(system.clone())
        .with_device_spec(device)
        .map_err(to_py_err)?;
    if let Some(frames) = chunk_frames {
        exec = exec.with_chunk_frames(frames);
    }
    let output = match traj {
        TrajKind::Dcd(reader) => exec.run_plan(plan, reader),
        TrajKind::Xtc(reader) => exec.run_plan(plan, reader),
    }
    .map_err(to_py_err)?;
    Ok(output)
}

fn matrix_to_py<'py>(
    py: Python<'py>,
    data: Vec<f32>,
    rows: usize,
    cols: usize,
) -> PyResult<&'py PyArray2<f32>> {
    if rows * cols != data.len() {
        return Err(PyRuntimeError::new_err("matrix shape mismatch"));
    }
    let array = Array2::from_shape_vec((rows, cols), data)
        .map_err(|_| PyRuntimeError::new_err("invalid matrix shape"))?;
    Ok(array.into_pyarray(py))
}

fn timeseries_to_py(
    py: Python<'_>,
    time: Vec<f32>,
    data: Vec<f32>,
    rows: usize,
    cols: usize,
) -> PyResult<PyObject> {
    if rows * cols != data.len() {
        return Err(PyRuntimeError::new_err("timeseries shape mismatch"));
    }
    let t = PyArray1::from_vec(py, time);
    let array = Array2::from_shape_vec((rows, cols), data)
        .map_err(|_| PyRuntimeError::new_err("invalid timeseries shape"))?;
    Ok((t, array.into_pyarray(py)).into_py(py))
}

fn hist_to_py(py: Python<'_>, centers: Vec<f32>, counts: Vec<u64>) -> PyObject {
    let centers = PyArray1::from_vec(py, centers);
    let counts = PyArray1::from_vec(py, counts);
    (centers, counts).into_py(py)
}

fn persistence_to_py(py: Python<'_>, output: traj_engine::PersistenceOutput) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item(
        "bond_autocorrelation",
        PyArray1::from_vec(py, output.bond_autocorrelation),
    )?;
    dict.set_item("lb", output.lb)?;
    dict.set_item("lp", output.lp)?;
    dict.set_item("fit", PyArray1::from_vec(py, output.fit))?;
    dict.set_item("kuhn_length", output.kuhn_length)?;
    Ok(dict.into_py(py))
}

fn dielectric_to_py(py: Python<'_>, output: traj_engine::DielectricOutput) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("time", PyArray1::from_vec(py, output.time))?;
    dict.set_item("rot_sq", PyArray1::from_vec(py, output.rot_sq))?;
    dict.set_item("trans_sq", PyArray1::from_vec(py, output.trans_sq))?;
    dict.set_item("rot_trans", PyArray1::from_vec(py, output.rot_trans))?;
    dict.set_item("dielectric_rot", output.dielectric_rot)?;
    dict.set_item("dielectric_total", output.dielectric_total)?;
    dict.set_item("mu_avg", output.mu_avg)?;
    Ok(dict.into_py(py))
}

fn structure_factor_to_py(
    py: Python<'_>,
    output: traj_engine::StructureFactorOutput,
) -> PyResult<PyObject> {
    let r = PyArray1::from_vec(py, output.r);
    let g = PyArray1::from_vec(py, output.g_r);
    let q = PyArray1::from_vec(py, output.q);
    let s = PyArray1::from_vec(py, output.s_q);
    Ok((r, g, q, s).into_py(py))
}

fn grid_to_py(py: Python<'_>, output: traj_engine::GridOutput) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("dims", vec![output.dims[0], output.dims[1], output.dims[2]])?;
    dict.set_item("mean", PyArray1::from_vec(py, output.mean))?;
    dict.set_item("std", PyArray1::from_vec(py, output.std))?;
    dict.set_item("first", PyArray1::from_vec(py, output.first))?;
    dict.set_item("last", PyArray1::from_vec(py, output.last))?;
    dict.set_item("min", PyArray1::from_vec(py, output.min))?;
    dict.set_item("max", PyArray1::from_vec(py, output.max))?;
    Ok(dict.into_py(py))
}

fn parse_reference(value: &str) -> PyResult<ReferenceMode> {
    match value {
        "topology" => Ok(ReferenceMode::Topology),
        "frame0" => Ok(ReferenceMode::Frame0),
        _ => Err(PyRuntimeError::new_err(
            "reference must be 'topology' or 'frame0'",
        )),
    }
}

fn parse_pbc(value: &str) -> PyResult<PbcMode> {
    match value {
        "orthorhombic" => Ok(PbcMode::Orthorhombic),
        "none" => Ok(PbcMode::None),
        _ => Err(PyRuntimeError::new_err(
            "pbc must be 'orthorhombic' or 'none'",
        )),
    }
}

fn parse_group_by(value: &str) -> PyResult<GroupBy> {
    GroupBy::parse(value).map_err(|err| PyRuntimeError::new_err(err.to_string()))
}

fn parse_lag_mode(value: &str) -> PyResult<LagMode> {
    match value {
        "auto" => Ok(LagMode::Auto),
        "multi_tau" | "multi-tau" => Ok(LagMode::MultiTau),
        "ring" => Ok(LagMode::Ring),
        "fft" => Ok(LagMode::Fft),
        _ => Err(PyRuntimeError::new_err(
            "lag_mode must be 'auto', 'multi_tau', 'ring', or 'fft'",
        )),
    }
}
