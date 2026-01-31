use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::FrameChunk;
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::executor::{Device, Plan, PlanOutput};
use crate::plans::polymer::common::{histogram_centers, PolymerChains};

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuPolymer};

pub struct BondAngleDistributionPlan {
    selection: Selection,
    bins: usize,
    degrees: bool,
    max_angle: f32,
    counts: Vec<u64>,
    centers: Vec<f32>,
    chains: Option<PolymerChains>,
    #[cfg(feature = "cuda")]
    gpu: Option<GpuPolymer>,
}

impl BondAngleDistributionPlan {
    pub fn new(selection: Selection, bins: usize, degrees: bool) -> Self {
        let max_angle = if degrees { 180.0 } else { std::f32::consts::PI };
        Self {
            selection,
            bins: bins.max(1),
            degrees,
            max_angle,
            counts: vec![0; bins.max(1)],
            centers: histogram_centers(max_angle, bins.max(1)),
            chains: None,
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }
}

impl Plan for BondAngleDistributionPlan {
    fn name(&self) -> &'static str {
        "polymer_bond_angle"
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        let _ = device;
        let chains = PolymerChains::from_selection(system, &self.selection)?;
        if chains.angle_triplets.is_empty() {
            return Err(TrajError::Mismatch("no angles in selection".into()));
        }
        self.counts.fill(0);
        self.chains = Some(chains);
        #[cfg(feature = "cuda")]
        {
            self.gpu = None;
            if let Device::Cuda(ctx) = device {
                let chains = self.chains.as_ref().unwrap();
                let gpu = ctx.polymer_data(
                    &chains.offsets,
                    &chains.indices,
                    None,
                    Some(&chains.angle_triplets),
                )?;
                self.gpu = Some(gpu);
            }
        }
        Ok(())
    }

    fn process_chunk(
        &mut self,
        chunk: &FrameChunk,
        _system: &System,
        device: &Device,
    ) -> TrajResult<()> {
        let _ = device;
        let chains = self.chains.as_ref().unwrap();
        let bin_width = self.max_angle / self.bins as f32;
        #[cfg(feature = "cuda")]
        if let (Device::Cuda(ctx), Some(gpu)) = (device, &self.gpu) {
            let coords = convert_coords(&chunk.coords);
            let mut counts = ctx.alloc_counts(self.bins)?;
            ctx.reset_counts(&mut counts)?;
            ctx.polymer_angle_hist(
                &coords,
                chunk.n_atoms,
                chunk.n_frames,
                gpu,
                self.max_angle,
                self.bins,
                self.degrees,
                &mut counts,
            )?;
            let local = ctx.read_counts(&counts)?;
            for (i, v) in local.into_iter().enumerate() {
                self.counts[i] += v;
            }
            return Ok(());
        }
        for frame in 0..chunk.n_frames {
            for trip in chains.angle_triplets.chunks(3) {
                let a = trip[0] as usize;
                let b = trip[1] as usize;
                let c = trip[2] as usize;
                let pa = chunk.coords[frame * chunk.n_atoms + a];
                let pb = chunk.coords[frame * chunk.n_atoms + b];
                let pc = chunk.coords[frame * chunk.n_atoms + c];
                let v1 = [pa[0] - pb[0], pa[1] - pb[1], pa[2] - pb[2]];
                let v2 = [pc[0] - pb[0], pc[1] - pb[1], pc[2] - pb[2]];
                let dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
                let n1 = (v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2]).sqrt();
                let n2 = (v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2]).sqrt();
                if n1 == 0.0 || n2 == 0.0 {
                    continue;
                }
                let mut angle = (dot / (n1 * n2)).clamp(-1.0, 1.0).acos();
                if self.degrees {
                    angle = angle.to_degrees();
                }
                if angle < self.max_angle {
                    let bin = (angle / bin_width) as usize;
                    if bin < self.bins {
                        self.counts[bin] += 1;
                    }
                }
            }
        }
        Ok(())
    }

    fn finalize(&mut self) -> TrajResult<PlanOutput> {
        Ok(PlanOutput::Histogram {
            centers: std::mem::take(&mut self.centers),
            counts: std::mem::take(&mut self.counts),
        })
    }
}
