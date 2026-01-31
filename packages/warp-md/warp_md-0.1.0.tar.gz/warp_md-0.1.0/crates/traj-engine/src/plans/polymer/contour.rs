use traj_core::error::TrajResult;
use traj_core::frame::FrameChunk;
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::executor::{Device, Plan, PlanOutput};
use crate::plans::polymer::common::PolymerChains;

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuPolymer};

pub struct ContourLengthPlan {
    selection: Selection,
    chains: Option<PolymerChains>,
    results: Vec<f32>,
    n_chains: usize,
    #[cfg(feature = "cuda")]
    gpu: Option<GpuPolymer>,
}

impl ContourLengthPlan {
    pub fn new(selection: Selection) -> Self {
        Self {
            selection,
            chains: None,
            results: Vec::new(),
            n_chains: 0,
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }

    pub fn n_chains(&self) -> usize {
        self.n_chains
    }
}

impl Plan for ContourLengthPlan {
    fn name(&self) -> &'static str {
        "polymer_contour_length"
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        let _ = device;
        self.results.clear();
        let chains = PolymerChains::from_selection(system, &self.selection)?;
        self.n_chains = chains.n_chains();
        self.chains = Some(chains);
        #[cfg(feature = "cuda")]
        {
            self.gpu = None;
            if let Device::Cuda(ctx) = device {
                let chains = self.chains.as_ref().unwrap();
                let gpu = ctx.polymer_data(&chains.offsets, &chains.indices, None, None)?;
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
        #[cfg(feature = "cuda")]
        if let (Device::Cuda(ctx), Some(gpu)) = (device, &self.gpu) {
            let coords = convert_coords(&chunk.coords);
            let out = ctx.polymer_contour_length(&coords, chunk.n_atoms, chunk.n_frames, gpu)?;
            self.results.extend(out);
            return Ok(());
        }
        for frame in 0..chunk.n_frames {
            for chain in &chains.chains {
                let mut sum = 0.0f32;
                for pair in chain.windows(2) {
                    let a = chunk.coords[frame * chunk.n_atoms + pair[0]];
                    let b = chunk.coords[frame * chunk.n_atoms + pair[1]];
                    let dx = b[0] - a[0];
                    let dy = b[1] - a[1];
                    let dz = b[2] - a[2];
                    sum += (dx * dx + dy * dy + dz * dz).sqrt();
                }
                self.results.push(sum);
            }
        }
        Ok(())
    }

    fn finalize(&mut self) -> TrajResult<PlanOutput> {
        let data = std::mem::take(&mut self.results);
        let rows = if self.n_chains > 0 {
            data.len() / self.n_chains
        } else {
            0
        };
        Ok(PlanOutput::Matrix {
            data,
            rows,
            cols: self.n_chains,
        })
    }
}
