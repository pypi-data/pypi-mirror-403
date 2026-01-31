use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::FrameChunk;
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::executor::{Device, Plan, PlanOutput};
use crate::plans::polymer::common::{histogram_centers, PolymerChains};

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuPolymer};

pub struct BondLengthDistributionPlan {
    selection: Selection,
    bins: usize,
    r_max: f32,
    counts: Vec<u64>,
    centers: Vec<f32>,
    chains: Option<PolymerChains>,
    #[cfg(feature = "cuda")]
    gpu: Option<GpuPolymer>,
}

impl BondLengthDistributionPlan {
    pub fn new(selection: Selection, bins: usize, r_max: f32) -> Self {
        Self {
            selection,
            bins: bins.max(1),
            r_max,
            counts: vec![0; bins.max(1)],
            centers: histogram_centers(r_max, bins.max(1)),
            chains: None,
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }
}

impl Plan for BondLengthDistributionPlan {
    fn name(&self) -> &'static str {
        "polymer_bond_length"
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        let _ = device;
        let chains = PolymerChains::from_selection(system, &self.selection)?;
        if chains.bond_pairs.is_empty() {
            return Err(TrajError::Mismatch("no bonds in selection".into()));
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
                    Some(&chains.bond_pairs),
                    None,
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
        let bin_width = self.r_max / self.bins as f32;
        #[cfg(feature = "cuda")]
        if let (Device::Cuda(ctx), Some(gpu)) = (device, &self.gpu) {
            let coords = convert_coords(&chunk.coords);
            let mut counts = ctx.alloc_counts(self.bins)?;
            ctx.reset_counts(&mut counts)?;
            ctx.polymer_bond_hist(
                &coords,
                chunk.n_atoms,
                chunk.n_frames,
                gpu,
                self.r_max,
                self.bins,
                &mut counts,
            )?;
            let local = ctx.read_counts(&counts)?;
            for (i, v) in local.into_iter().enumerate() {
                self.counts[i] += v;
            }
            return Ok(());
        }
        for frame in 0..chunk.n_frames {
            for pair in chains.bond_pairs.chunks(2) {
                let a = pair[0] as usize;
                let b = pair[1] as usize;
                let pa = chunk.coords[frame * chunk.n_atoms + a];
                let pb = chunk.coords[frame * chunk.n_atoms + b];
                let dx = pb[0] - pa[0];
                let dy = pb[1] - pa[1];
                let dz = pb[2] - pa[2];
                let r = (dx * dx + dy * dy + dz * dz).sqrt();
                if r < self.r_max {
                    let bin = (r / bin_width) as usize;
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
