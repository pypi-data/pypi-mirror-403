use traj_core::error::TrajResult;
use traj_core::frame::FrameChunk;
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::executor::{Device, Plan, PlanOutput};

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuSelection};

pub struct RgPlan {
    selection: Selection,
    mass_weighted: bool,
    results: Vec<f32>,
    #[cfg(feature = "cuda")]
    gpu: Option<RgGpuState>,
}

#[cfg(feature = "cuda")]
struct RgGpuState {
    selection: GpuSelection,
}

impl RgPlan {
    pub fn new(selection: Selection, mass_weighted: bool) -> Self {
        Self {
            selection,
            mass_weighted,
            results: Vec::new(),
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }
}

impl Plan for RgPlan {
    fn name(&self) -> &'static str {
        "rg"
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        self.results.clear();
        let _ = device;
        let _ = system;
        #[cfg(feature = "cuda")]
        {
            self.gpu = None;
            if let Device::Cuda(ctx) = device {
                let masses = if self.mass_weighted {
                    Some(
                        self.selection
                            .indices
                            .iter()
                            .map(|idx| system.atoms.mass[*idx as usize])
                            .collect::<Vec<_>>(),
                    )
                } else {
                    None
                };
                let selection = ctx.selection(&self.selection.indices, masses.as_deref())?;
                self.gpu = Some(RgGpuState { selection });
            }
        }
        Ok(())
    }

    fn process_chunk(
        &mut self,
        chunk: &FrameChunk,
        system: &System,
        device: &Device,
    ) -> TrajResult<()> {
        let _ = device;
        #[cfg(feature = "cuda")]
        if let (Device::Cuda(ctx), Some(gpu)) = (device, &self.gpu) {
            let coords = convert_coords(&chunk.coords);
            let results =
                ctx.rg(&coords, chunk.n_atoms, chunk.n_frames, &gpu.selection, self.mass_weighted)?;
            self.results.extend(results);
            return Ok(());
        }
        let n_atoms = chunk.n_atoms;
        let sel = &self.selection.indices;
        for frame in 0..chunk.n_frames {
            let mut com = [0.0f32; 3];
            let mut mass_sum = 0.0f32;
            for &idx in sel.iter() {
                let atom_idx = idx as usize;
                let mass = if self.mass_weighted {
                    system.atoms.mass[atom_idx]
                } else {
                    1.0
                };
                let pos = chunk.coords[frame * n_atoms + atom_idx];
                com[0] += pos[0] * mass;
                com[1] += pos[1] * mass;
                com[2] += pos[2] * mass;
                mass_sum += mass;
            }
            if mass_sum == 0.0 {
                self.results.push(0.0);
                continue;
            }
            com[0] /= mass_sum;
            com[1] /= mass_sum;
            com[2] /= mass_sum;
            let mut sum = 0.0f32;
            for &idx in sel.iter() {
                let atom_idx = idx as usize;
                let mass = if self.mass_weighted {
                    system.atoms.mass[atom_idx]
                } else {
                    1.0
                };
                let pos = chunk.coords[frame * n_atoms + atom_idx];
                let dx = pos[0] - com[0];
                let dy = pos[1] - com[1];
                let dz = pos[2] - com[2];
                sum += mass * (dx * dx + dy * dy + dz * dz);
            }
            let rg = (sum / mass_sum).sqrt();
            self.results.push(rg);
        }
        Ok(())
    }

    fn finalize(&mut self) -> TrajResult<PlanOutput> {
        Ok(PlanOutput::Series(std::mem::take(&mut self.results)))
    }
}
