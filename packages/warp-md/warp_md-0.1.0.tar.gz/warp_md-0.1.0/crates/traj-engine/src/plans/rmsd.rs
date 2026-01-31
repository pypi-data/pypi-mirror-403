use nalgebra::{Matrix3, Vector3};

use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::FrameChunk;
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::executor::{Device, Plan, PlanOutput};
use crate::plans::ReferenceMode;

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuReference, GpuSelection};

pub struct RmsdPlan {
    selection: Selection,
    align: bool,
    reference_mode: ReferenceMode,
    reference: Option<Vec<[f32; 4]>>,
    results: Vec<f32>,
    #[cfg(feature = "cuda")]
    gpu: Option<RmsdGpuState>,
}

#[cfg(feature = "cuda")]
struct RmsdGpuState {
    selection: GpuSelection,
    reference: GpuReference,
}

impl RmsdPlan {
    pub fn new(selection: Selection, reference_mode: ReferenceMode, align: bool) -> Self {
        Self {
            selection,
            align,
            reference_mode,
            reference: None,
            results: Vec::new(),
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }
}

impl Plan for RmsdPlan {
    fn name(&self) -> &'static str {
        "rmsd"
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        self.results.clear();
        let _ = device;
        #[cfg(feature = "cuda")]
        {
            self.gpu = None;
        }
        match self.reference_mode {
            ReferenceMode::Topology => {
                let positions0 = system
                    .positions0
                    .as_ref()
                    .ok_or_else(|| TrajError::Mismatch("no topology reference coords".into()))?;
                let mut reference = Vec::with_capacity(self.selection.indices.len());
                for &idx in self.selection.indices.iter() {
                    reference.push(positions0[idx as usize]);
                }
                self.reference = Some(reference);
            }
            ReferenceMode::Frame0 => {
                self.reference = None;
            }
        }
        #[cfg(feature = "cuda")]
        if let (Device::Cuda(ctx), Some(reference)) = (device, self.reference.as_ref()) {
            let selection = ctx.selection(&self.selection.indices, None)?;
            let reference_gpu = ctx.reference(&convert_coords(reference))?;
            self.gpu = Some(RmsdGpuState {
                selection,
                reference: reference_gpu,
            });
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
        let n_atoms = chunk.n_atoms;
        if self.reference.is_none() && matches!(self.reference_mode, ReferenceMode::Frame0) {
            if chunk.n_frames == 0 {
                return Ok(());
            }
            let mut reference = Vec::with_capacity(self.selection.indices.len());
            for &idx in self.selection.indices.iter() {
                reference.push(chunk.coords[idx as usize]);
            }
            self.reference = Some(reference);
            #[cfg(feature = "cuda")]
            if let Device::Cuda(ctx) = device {
                let selection = ctx.selection(&self.selection.indices, None)?;
                let reference_gpu = ctx.reference(&convert_coords(self.reference.as_ref().unwrap()))?;
                self.gpu = Some(RmsdGpuState {
                    selection,
                    reference: reference_gpu,
                });
            }
        }

        let reference = self
            .reference
            .as_ref()
            .ok_or_else(|| TrajError::Mismatch("reference not initialized".into()))?;

        #[cfg(feature = "cuda")]
        if let (Device::Cuda(ctx), Some(gpu)) = (device, &self.gpu) {
            let coords = convert_coords(&chunk.coords);
            if self.align {
                let cov = ctx.rmsd_covariance(
                    &coords,
                    n_atoms,
                    chunk.n_frames,
                    &gpu.selection,
                    &gpu.reference,
                )?;
                let n_sel = gpu.selection.n_sel();
                for frame in 0..chunk.n_frames {
                    let rmsd = rmsd_from_cov(
                        &cov.cov[frame],
                        cov.sum_x2[frame] as f64,
                        cov.sum_y2[frame] as f64,
                        n_sel,
                    );
                    self.results.push(rmsd);
                }
            } else {
                let results =
                    ctx.rmsd_raw(&coords, n_atoms, chunk.n_frames, &gpu.selection, &gpu.reference)?;
                self.results.extend(results);
            }
            return Ok(());
        }

        for frame in 0..chunk.n_frames {
            let mut frame_coords = Vec::with_capacity(self.selection.indices.len());
            for &idx in self.selection.indices.iter() {
                frame_coords.push(chunk.coords[frame * n_atoms + idx as usize]);
            }
            let rmsd = if self.align {
                rmsd_aligned(&frame_coords, reference)
            } else {
                rmsd_raw(&frame_coords, reference)
            };
            self.results.push(rmsd);
        }
        Ok(())
    }

    fn finalize(&mut self) -> TrajResult<PlanOutput> {
        Ok(PlanOutput::Series(std::mem::take(&mut self.results)))
    }
}

fn rmsd_raw(frame: &[[f32; 4]], reference: &[[f32; 4]]) -> f32 {
    let mut sum = 0.0f64;
    let n = frame.len().min(reference.len());
    for i in 0..n {
        let dx = frame[i][0] as f64 - reference[i][0] as f64;
        let dy = frame[i][1] as f64 - reference[i][1] as f64;
        let dz = frame[i][2] as f64 - reference[i][2] as f64;
        sum += dx * dx + dy * dy + dz * dz;
    }
    ((sum / n as f64).sqrt()) as f32
}

fn rmsd_aligned(frame: &[[f32; 4]], reference: &[[f32; 4]]) -> f32 {
    let n = frame.len().min(reference.len());
    if n == 0 {
        return 0.0;
    }
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for i in 0..n {
        x.push(Vector3::new(
            frame[i][0] as f64,
            frame[i][1] as f64,
            frame[i][2] as f64,
        ));
        y.push(Vector3::new(
            reference[i][0] as f64,
            reference[i][1] as f64,
            reference[i][2] as f64,
        ));
    }
    let cx = centroid(&x);
    let cy = centroid(&y);
    let mut h = Matrix3::zeros();
    for i in 0..n {
        let xr = x[i] - cx;
        let yr = y[i] - cy;
        h += xr * yr.transpose();
    }
    let svd = h.svd(true, true);
    let (u, v_t) = match (svd.u, svd.v_t) {
        (Some(u), Some(v_t)) => (u, v_t),
        _ => return rmsd_raw(frame, reference),
    };
    let mut r = v_t.transpose() * u.transpose();
    if r.determinant() < 0.0 {
        let mut v_t_adj = v_t;
        v_t_adj.row_mut(2).neg_mut();
        r = v_t_adj.transpose() * u.transpose();
    }
    let mut sum = 0.0f64;
    for i in 0..n {
        let xr = x[i] - cx;
        let yr = y[i] - cy;
        let aligned = r * xr;
        let diff = aligned - yr;
        sum += diff.dot(&diff);
    }
    ((sum / n as f64).sqrt()) as f32
}

#[cfg(feature = "cuda")]
fn rmsd_from_cov(cov: &[f32; 9], sum_x2: f64, sum_y2: f64, n_sel: usize) -> f32 {
    if n_sel == 0 {
        return 0.0;
    }
    let cov_f64 = [
        cov[0] as f64,
        cov[1] as f64,
        cov[2] as f64,
        cov[3] as f64,
        cov[4] as f64,
        cov[5] as f64,
        cov[6] as f64,
        cov[7] as f64,
        cov[8] as f64,
    ];
    let m = Matrix3::from_row_slice(&cov_f64);
    let svd = m.svd(true, true);
    let mut sigma_sum = svd.singular_values[0] + svd.singular_values[1] + svd.singular_values[2];
    if let (Some(u), Some(v_t)) = (svd.u, svd.v_t) {
        let det = (v_t.transpose() * u.transpose()).determinant();
        if det < 0.0 {
            sigma_sum -= 2.0 * svd.singular_values[2];
        }
    }
    let n = n_sel as f64;
    let rmsd2 = (sum_x2 + sum_y2 - 2.0 * sigma_sum) / n;
    if rmsd2 <= 0.0 {
        0.0
    } else {
        rmsd2.sqrt() as f32
    }
}

fn centroid(points: &[Vector3<f64>]) -> Vector3<f64> {
    let mut c = Vector3::new(0.0, 0.0, 0.0);
    for p in points {
        c += p;
    }
    c / (points.len() as f64)
}
