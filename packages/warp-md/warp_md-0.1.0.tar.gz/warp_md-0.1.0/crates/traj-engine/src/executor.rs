use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::{FrameChunk, FrameChunkBuilder};
use traj_core::system::System;
use traj_io::TrajReader;

#[cfg(feature = "cuda")]
use traj_gpu::GpuContext;

#[derive(Clone)]
pub enum Device {
    Cpu,
    #[cfg(feature = "cuda")]
    Cuda(GpuContext),
}

impl Device {
    pub fn cpu() -> Self {
        Device::Cpu
    }

    pub fn from_spec(spec: &str) -> TrajResult<Self> {
        let spec = spec.trim();
        if spec.eq_ignore_ascii_case("cpu") {
            return Ok(Device::Cpu);
        }
        if spec.eq_ignore_ascii_case("auto") {
            #[cfg(feature = "cuda")]
            {
                if let Ok(ctx) = GpuContext::new(0) {
                    return Ok(Device::Cuda(ctx));
                }
            }
            return Ok(Device::Cpu);
        }
        if spec.to_ascii_lowercase().starts_with("cuda") {
            #[cfg(feature = "cuda")]
            {
                let idx = parse_cuda_index(spec)?;
                return Ok(Device::Cuda(GpuContext::new(idx)?));
            }
            #[cfg(not(feature = "cuda"))]
            {
                return Err(TrajError::Unsupported(
                    "cuda feature disabled; rebuild with --features cuda".into(),
                ));
            }
        }
        Err(TrajError::Unsupported(format!(
            "unknown device spec '{spec}'"
        )))
    }
}

#[cfg(feature = "cuda")]
fn parse_cuda_index(spec: &str) -> TrajResult<usize> {
    let parts: Vec<&str> = spec.split(':').collect();
    if parts.len() == 1 {
        return Ok(0);
    }
    if parts.len() == 2 {
        return parts[1]
            .parse()
            .map_err(|_| TrajError::Parse(format!("invalid cuda device spec '{spec}'")));
    }
    Err(TrajError::Parse(format!(
        "invalid cuda device spec '{spec}'"
    )))
}

pub struct Executor {
    system: System,
    chunk_frames: usize,
    device: Device,
}

impl Executor {
    pub fn new(system: System) -> Self {
        Self {
            system,
            chunk_frames: 128,
            device: Device::Cpu,
        }
    }

    pub fn with_chunk_frames(mut self, chunk_frames: usize) -> Self {
        self.chunk_frames = chunk_frames.max(1);
        self
    }

    pub fn with_device(mut self, device: Device) -> Self {
        self.device = device;
        self
    }

    pub fn with_device_spec(mut self, spec: &str) -> TrajResult<Self> {
        self.device = Device::from_spec(spec)?;
        Ok(self)
    }

    pub fn system(&self) -> &System {
        &self.system
    }

    pub fn system_mut(&mut self) -> &mut System {
        &mut self.system
    }

    pub fn run_plan<P: Plan>(&mut self, plan: &mut P, traj: &mut dyn TrajReader) -> TrajResult<PlanOutput> {
        if traj.n_atoms() != self.system.n_atoms() {
            return Err(TrajError::Mismatch(
                "trajectory atom count does not match system".into(),
            ));
        }
        plan.set_frames_hint(traj.n_frames_hint());
        plan.init(&self.system, &self.device)?;
        let mut builder = FrameChunkBuilder::new(self.system.n_atoms(), self.chunk_frames);
        loop {
            let frames = traj.read_chunk(self.chunk_frames, &mut builder)?;
            if frames == 0 {
                break;
            }
            let chunk = builder.finish()?;
            plan.process_chunk(&chunk, &self.system, &self.device)?;
        }
        plan.finalize()
    }
}

pub trait Plan {
    fn name(&self) -> &'static str;
    fn set_frames_hint(&mut self, _n_frames: Option<usize>) {}
    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()>;
    fn process_chunk(&mut self, chunk: &FrameChunk, system: &System, device: &Device) -> TrajResult<()>;
    fn finalize(&mut self) -> TrajResult<PlanOutput>;
}

pub enum PlanOutput {
    Series(Vec<f32>),
    Matrix { data: Vec<f32>, rows: usize, cols: usize },
    Histogram { centers: Vec<f32>, counts: Vec<u64> },
    Rdf(RdfOutput),
    Persistence(PersistenceOutput),
    TimeSeries { time: Vec<f32>, data: Vec<f32>, rows: usize, cols: usize },
    Dielectric(DielectricOutput),
    StructureFactor(StructureFactorOutput),
    Grid(GridOutput),
}

pub struct RdfOutput {
    pub r: Vec<f32>,
    pub g_r: Vec<f32>,
    pub counts: Vec<u64>,
}

pub struct PersistenceOutput {
    pub bond_autocorrelation: Vec<f32>,
    pub lb: f32,
    pub lp: f32,
    pub fit: Vec<f32>,
    pub kuhn_length: f32,
}

pub struct DielectricOutput {
    pub time: Vec<f32>,
    pub rot_sq: Vec<f32>,
    pub trans_sq: Vec<f32>,
    pub rot_trans: Vec<f32>,
    pub dielectric_rot: f32,
    pub dielectric_total: f32,
    pub mu_avg: f32,
}

pub struct StructureFactorOutput {
    pub r: Vec<f32>,
    pub g_r: Vec<f32>,
    pub q: Vec<f32>,
    pub s_q: Vec<f32>,
}

pub struct GridOutput {
    pub dims: [usize; 3],
    pub mean: Vec<f32>,
    pub std: Vec<f32>,
    pub first: Vec<u32>,
    pub last: Vec<u32>,
    pub min: Vec<u32>,
    pub max: Vec<u32>,
}
