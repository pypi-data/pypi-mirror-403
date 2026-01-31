use traj_core::error::TrajResult;
use traj_core::frame::{Box3, FrameChunk};
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::correlators::{LagMode, LagSettings};
use crate::correlators::multi_tau::MultiTauBuffer;
use crate::correlators::ring::RingBuffer;
use crate::executor::{Device, Plan, PlanOutput};
use crate::plans::analysis::grouping::{GroupBy, GroupMap, GroupSpec};
#[cfg(feature = "cuda")]
use crate::plans::analysis::common::groups_to_csr;

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuBufferF32, GpuContext, GpuGroups};

#[derive(Clone, Copy)]
pub struct FrameDecimation {
    pub start: usize,
    pub stride: usize,
}

#[derive(Clone, Copy)]
pub struct DtDecimation {
    pub cut1: usize,
    pub stride1: usize,
    pub cut2: usize,
    pub stride2: usize,
}

#[derive(Clone, Copy)]
pub struct TimeBinning {
    pub eps_num: f64,
    pub eps_add: f64,
}

impl Default for TimeBinning {
    fn default() -> Self {
        Self {
            eps_num: 1.0e-5,
            eps_add: 1.0e-4,
        }
    }
}

pub struct MsdPlan {
    selection: Selection,
    group_by: GroupBy,
    group_types: Option<Vec<usize>>,
    axis: Option<[f64; 3]>,
    length_scale: f64,
    frame_decimation: Option<FrameDecimation>,
    dt_decimation: Option<DtDecimation>,
    time_binning: TimeBinning,
    lag: LagSettings,
    frames_hint: Option<usize>,
    resolved_mode: LagMode,
    groups: Option<GroupMap>,
    type_ids: Vec<usize>,
    type_counts: Vec<usize>,
    n_groups: usize,
    n_atoms: usize,
    masses: Vec<f64>,
    dt0: Option<f64>,
    uniform_time: bool,
    last_time: Option<f64>,
    frame_index: usize,
    samples_seen: usize,
    last_wrapped: Vec<[f64; 3]>,
    wrapped_curr: Vec<[f64; 3]>,
    unwrap_prev: Vec<[f64; 3]>,
    unwrap_curr: Vec<[f64; 3]>,
    sample_f32: Vec<f32>,
    lags: Vec<usize>,
    acc: Vec<f64>,
    multi_tau: Option<MultiTauBuffer>,
    ring: Option<RingBuffer>,
    series: Vec<f32>,
    #[cfg(feature = "cuda")]
    gpu: Option<MsdGpuState>,
}

#[cfg(feature = "cuda")]
struct MsdGpuState {
    ctx: GpuContext,
    groups: GpuGroups,
    masses: GpuBufferF32,
}

impl MsdPlan {
    pub fn new(selection: Selection, group_by: GroupBy) -> Self {
        Self {
            selection,
            group_by,
            group_types: None,
            axis: None,
            length_scale: 1.0,
            frame_decimation: None,
            dt_decimation: None,
            time_binning: TimeBinning::default(),
            lag: LagSettings::default(),
            frames_hint: None,
            resolved_mode: LagMode::Auto,
            groups: None,
            type_ids: Vec::new(),
            type_counts: Vec::new(),
            n_groups: 0,
            n_atoms: 0,
            masses: Vec::new(),
            dt0: None,
            uniform_time: true,
            last_time: None,
            frame_index: 0,
            samples_seen: 0,
            last_wrapped: Vec::new(),
            wrapped_curr: Vec::new(),
            unwrap_prev: Vec::new(),
            unwrap_curr: Vec::new(),
            sample_f32: Vec::new(),
            lags: Vec::new(),
            acc: Vec::new(),
            multi_tau: None,
            ring: None,
            series: Vec::new(),
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }

    pub fn with_axis(mut self, axis: [f64; 3]) -> Self {
        let norm = (axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2]).sqrt();
        if norm > 0.0 {
            self.axis = Some([axis[0] / norm, axis[1] / norm, axis[2] / norm]);
        } else {
            self.axis = Some(axis);
        }
        self
    }

    pub fn with_length_scale(mut self, scale: f64) -> Self {
        self.length_scale = scale;
        self
    }

    pub fn with_frame_decimation(mut self, dec: FrameDecimation) -> Self {
        self.frame_decimation = Some(dec);
        self
    }

    pub fn with_dt_decimation(mut self, dec: DtDecimation) -> Self {
        self.dt_decimation = Some(dec);
        self
    }

    pub fn with_time_binning(mut self, bin: TimeBinning) -> Self {
        self.time_binning = bin;
        self
    }

    pub fn with_group_types(mut self, types: Vec<usize>) -> Self {
        self.group_types = Some(types);
        self
    }

    pub fn with_lag_mode(mut self, mode: LagMode) -> Self {
        self.lag = self.lag.with_mode(mode);
        self
    }

    pub fn with_max_lag(mut self, max_lag: usize) -> Self {
        self.lag = self.lag.with_max_lag(max_lag);
        self
    }

    pub fn with_memory_budget_bytes(mut self, budget: usize) -> Self {
        self.lag = self.lag.with_memory_budget_bytes(budget);
        self
    }

    pub fn with_multi_tau_m(mut self, m: usize) -> Self {
        self.lag = self.lag.with_multi_tau_m(m);
        self
    }

    pub fn with_multi_tau_levels(mut self, levels: usize) -> Self {
        self.lag = self.lag.with_multi_tau_levels(levels);
        self
    }
}

impl Plan for MsdPlan {
    fn name(&self) -> &'static str {
        "msd_multi"
    }

    fn set_frames_hint(&mut self, n_frames: Option<usize>) {
        self.frames_hint = n_frames;
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        self.n_atoms = system.n_atoms();
        let mut spec = GroupSpec::new(self.selection.clone(), self.group_by);
        if let Some(types) = &self.group_types {
            spec = spec.with_group_types(types.clone());
        }
        let groups = spec.build(system)?;
        self.n_groups = groups.n_groups();
        self.type_ids = groups.type_ids();
        self.type_counts = groups.type_counts();
        self.groups = Some(groups);
        self.masses = system.atoms.mass.iter().map(|m| *m as f64).collect();

        self.dt0 = None;
        self.uniform_time = true;
        self.last_time = None;
        self.frame_index = 0;
        self.samples_seen = 0;
        self.last_wrapped = vec![[0.0; 3]; self.n_groups];
        self.wrapped_curr = vec![[0.0; 3]; self.n_groups];
        self.unwrap_prev = vec![[0.0; 3]; self.n_groups];
        self.unwrap_curr = vec![[0.0; 3]; self.n_groups];
        self.sample_f32 = vec![0.0f32; self.n_groups * 3];
        self.lags.clear();
        self.acc.clear();
        self.multi_tau = None;
        self.ring = None;
        self.series.clear();

        let mut resolved_mode = self.lag.mode;
        if resolved_mode == LagMode::Auto {
            let use_fft = if let Some(n_frames) = self.frames_hint {
                self.lag.fft_fits(n_frames, self.n_groups, 3, 4)
            } else {
                false
            };
            resolved_mode = if use_fft { LagMode::Fft } else { LagMode::MultiTau };
        }
        self.resolved_mode = resolved_mode;

        match self.resolved_mode {
            LagMode::MultiTau => {
                let buffer = MultiTauBuffer::new(self.n_groups, 3, self.lag.multi_tau_m, self.lag.multi_tau_max_levels);
                self.lags = buffer.out_lags().to_vec();
                let cols = msd_cols(self.axis, self.type_counts.len());
                self.acc = vec![0.0f64; self.lags.len() * cols];
                self.multi_tau = Some(buffer);
            }
            LagMode::Ring => {
                let max_lag = self.lag.ring_max_lag_capped(self.n_groups, 3, 4);
                let buffer = RingBuffer::new(self.n_groups, 3, max_lag);
                self.lags = (1..=max_lag).collect();
                let cols = msd_cols(self.axis, self.type_counts.len());
                self.acc = vec![0.0f64; self.lags.len() * cols];
                self.ring = Some(buffer);
            }
            LagMode::Fft => {
                let capacity = self
                    .frames_hint
                    .unwrap_or(0)
                    .saturating_mul(self.n_groups)
                    .saturating_mul(3);
                self.series = Vec::with_capacity(capacity);
            }
            LagMode::Auto => {}
        }

        #[cfg(feature = "cuda")]
        {
            self.gpu = None;
            if let Device::Cuda(ctx) = device {
                let (offsets, indices, max_len) = groups_to_csr(&self.groups.as_ref().unwrap().groups);
                let groups = ctx.groups(&offsets, &indices, max_len)?;
                let masses: Vec<f32> = system.atoms.mass.iter().map(|m| *m).collect();
                let masses = ctx.upload_f32(&masses)?;
                self.gpu = Some(MsdGpuState {
                    ctx: ctx.clone(),
                    groups,
                    masses,
                });
            }
        }
        #[cfg(not(feature = "cuda"))]
        let _ = device;

        Ok(())
    }

    fn process_chunk(
        &mut self,
        chunk: &FrameChunk,
        _system: &System,
        _device: &Device,
    ) -> TrajResult<()> {
        if self.n_groups == 0 {
            return Ok(());
        }

        let n_frames = chunk.n_frames;
        if n_frames == 0 {
            return Ok(());
        }

        #[cfg(feature = "cuda")]
        let mut used_gpu = false;
        #[cfg(not(feature = "cuda"))]
        let used_gpu = false;
        #[cfg(feature = "cuda")]
        let com_gpu = {
            if let Some(gpu) = &self.gpu {
                let coords = convert_coords(&chunk.coords);
                let com = gpu.ctx.group_com(
                    &coords,
                    self.n_atoms,
                    n_frames,
                    &gpu.groups,
                    &gpu.masses,
                    self.length_scale as f32,
                )?;
                used_gpu = true;
                Some(com)
            } else {
                None
            }
        };
        #[cfg(not(feature = "cuda"))]
        let _com_gpu = ();

        for frame in 0..n_frames {
            self.frame_index += 1;
            if let Some(dec) = self.frame_decimation {
                let idx1 = self.frame_index;
                if idx1 > dec.start && (idx1 % dec.stride) != 0 {
                    continue;
                }
            }

            let time = if let Some(times) = &chunk.time_ps {
                times[frame] as f64
            } else {
                (self.frame_index - 1) as f64
            };
            if let Some(last) = self.last_time {
                let dt = time - last;
                if let Some(dt0) = self.dt0 {
                    if (dt - dt0).abs() > self.time_binning.eps_num.max(1.0e-6) {
                        self.uniform_time = false;
                    }
                } else if dt > 0.0 {
                    self.dt0 = Some(dt);
                }
            }
            self.last_time = Some(time);

            if used_gpu {
                #[cfg(feature = "cuda")]
                {
                    let com = com_gpu.as_ref().unwrap();
                    for g in 0..self.n_groups {
                        let v = com[frame * self.n_groups + g];
                        self.wrapped_curr[g] = [v.x as f64, v.y as f64, v.z as f64];
                    }
                }
            } else {
                let frame_offset = frame * self.n_atoms;
                for (g_idx, atoms) in self.groups.as_ref().unwrap().groups.iter().enumerate() {
                    let mut sum = [0.0f64; 3];
                    let mut mass_sum = 0.0f64;
                    for &atom_idx in atoms {
                        let p = chunk.coords[frame_offset + atom_idx];
                        let m = self.masses[atom_idx];
                        sum[0] += (p[0] as f64) * m;
                        sum[1] += (p[1] as f64) * m;
                        sum[2] += (p[2] as f64) * m;
                        mass_sum += m;
                    }
                    let inv = if mass_sum > 0.0 { 1.0 / mass_sum } else { 0.0 };
                    self.wrapped_curr[g_idx][0] = sum[0] * inv * self.length_scale;
                    self.wrapped_curr[g_idx][1] = sum[1] * inv * self.length_scale;
                    self.wrapped_curr[g_idx][2] = sum[2] * inv * self.length_scale;
                }
            }

            if self.samples_seen == 0 {
                self.last_wrapped.copy_from_slice(&self.wrapped_curr);
                self.unwrap_prev.copy_from_slice(&self.wrapped_curr);
                self.unwrap_curr.copy_from_slice(&self.wrapped_curr);
            } else {
                let box_l = box_lengths(&chunk.box_[frame])
                    .map(|b| [b[0] * self.length_scale, b[1] * self.length_scale, b[2] * self.length_scale]);
                for g in 0..self.n_groups {
                    let curr = self.wrapped_curr[g];
                    let prev = self.last_wrapped[g];
                    let mut diff = [curr[0] - prev[0], curr[1] - prev[1], curr[2] - prev[2]];
                    if let Some(b) = box_l {
                        for k in 0..3 {
                            let l = b[k];
                            if l > 0.0 {
                                diff[k] -= (diff[k] / l).round() * l;
                            }
                        }
                    }
                    self.unwrap_curr[g][0] = self.unwrap_prev[g][0] + diff[0];
                    self.unwrap_curr[g][1] = self.unwrap_prev[g][1] + diff[1];
                    self.unwrap_curr[g][2] = self.unwrap_prev[g][2] + diff[2];
                }
                self.unwrap_prev.copy_from_slice(&self.unwrap_curr);
                self.last_wrapped.copy_from_slice(&self.wrapped_curr);
            }

            for g in 0..self.n_groups {
                let base = g * 3;
                self.sample_f32[base] = self.unwrap_curr[g][0] as f32;
                self.sample_f32[base + 1] = self.unwrap_curr[g][1] as f32;
                self.sample_f32[base + 2] = self.unwrap_curr[g][2] as f32;
            }

            match self.resolved_mode {
                LagMode::MultiTau => {
                    if let Some(buffer) = &mut self.multi_tau {
                        let axis = self.axis;
                        let cols = msd_cols(axis, self.type_counts.len());
                        let type_ids = &self.type_ids;
                        let type_counts = &self.type_counts;
                        let n_groups = self.n_groups;
                        let dt_dec = self.dt_decimation;
                        let lags = &self.lags;
                        let acc = &mut self.acc;
                        buffer.update(&self.sample_f32, |lag_idx, cur, old| {
                            let lag = lags[lag_idx];
                            if !lag_allowed(lag, dt_dec) {
                                return;
                            }
                            accumulate_msd(
                                acc,
                                lag_idx,
                                cols,
                                axis,
                                n_groups,
                                type_ids,
                                type_counts,
                                cur,
                                old,
                            );
                        });
                    }
                }
                LagMode::Ring => {
                    if let Some(buffer) = &mut self.ring {
                        let axis = self.axis;
                        let cols = msd_cols(axis, self.type_counts.len());
                        let type_ids = &self.type_ids;
                        let type_counts = &self.type_counts;
                        let n_groups = self.n_groups;
                        let dt_dec = self.dt_decimation;
                        let acc = &mut self.acc;
                        buffer.update(&self.sample_f32, |lag, cur, old| {
                            if !lag_allowed(lag, dt_dec) {
                                return;
                            }
                            let lag_idx = lag - 1;
                            accumulate_msd(
                                acc,
                                lag_idx,
                                cols,
                                axis,
                                n_groups,
                                type_ids,
                                type_counts,
                                cur,
                                old,
                            );
                        });
                    }
                }
                LagMode::Fft => {
                    self.series.extend_from_slice(&self.sample_f32);
                }
                LagMode::Auto => {}
            }

            self.samples_seen += 1;
        }

        Ok(())
    }

    fn finalize(&mut self) -> TrajResult<PlanOutput> {
        let n_frames = if self.resolved_mode == LagMode::Fft {
            if self.n_groups == 0 {
                0
            } else {
                self.series.len() / (self.n_groups * 3)
            }
        } else {
            self.samples_seen
        };

        if n_frames < 2 || self.n_groups == 0 {
            return Ok(PlanOutput::TimeSeries {
                time: Vec::new(),
                data: Vec::new(),
                rows: 0,
                cols: 0,
            });
        }

        let dt0 = self.dt0.unwrap_or(1.0);
        let n_types = self.type_counts.len();
        let cols = msd_cols(self.axis, n_types);

        match self.resolved_mode {
            LagMode::Fft => {
                if self.uniform_time {
                    #[cfg(feature = "cuda")]
                    if let Some(gpu) = &self.gpu {
                        let ndframe = n_frames.saturating_sub(1);
                        if ndframe > 0 {
                            let times_f32: Vec<f32> = (0..n_frames)
                                .map(|i| (dt0 * i as f64) as f32)
                                .collect();
                            let type_ids_u32: Vec<u32> =
                                self.type_ids.iter().map(|t| *t as u32).collect();
                            let type_counts_u32: Vec<u32> =
                                self.type_counts.iter().map(|c| *c as u32).collect();
                            let axis_f32 =
                                self.axis.map(|a| [a[0] as f32, a[1] as f32, a[2] as f32]);
                            let time_binning = (
                                self.time_binning.eps_num as f32,
                                self.time_binning.eps_add as f32,
                            );
                            let (msd_gpu, n_diff_gpu) = gpu.ctx.msd_time_lag(
                                &self.series,
                                &times_f32,
                                &type_ids_u32,
                                &type_counts_u32,
                                self.n_groups,
                                n_types,
                                ndframe,
                                axis_f32,
                                None,
                                self.dt_decimation.map(|d| (d.cut1, d.stride1, d.cut2, d.stride2)),
                                time_binning,
                            )?;
                            if !msd_gpu.is_empty() && !n_diff_gpu.is_empty() {
                                let mut lags = Vec::new();
                                for lag in 1..=ndframe {
                                    if lag_allowed(lag, self.dt_decimation) {
                                        lags.push(lag);
                                    }
                                }
                                let mut time = Vec::with_capacity(lags.len());
                                let mut data = vec![0.0f32; lags.len() * cols];
                                for (idx, &lag) in lags.iter().enumerate() {
                                    time.push((dt0 * lag as f64) as f32);
                                    let count = n_diff_gpu[lag] as f64;
                                    if count == 0.0 {
                                        continue;
                                    }
                                    let base = lag * cols;
                                    let out_base = idx * cols;
                                    for c in 0..cols {
                                        data[out_base + c] =
                                            (msd_gpu[base + c] as f64 / count) as f32;
                                    }
                                }
                                return Ok(PlanOutput::TimeSeries {
                                    time,
                                    data,
                                    rows: lags.len(),
                                    cols,
                                });
                            }
                        }
                    }
                }
                if !self.uniform_time {
                    let mut buffer = MultiTauBuffer::new(
                        self.n_groups,
                        3,
                        self.lag.multi_tau_m,
                        self.lag.multi_tau_max_levels,
                    );
                    let lags = buffer.out_lags().to_vec();
                    let mut acc = vec![0.0f64; lags.len() * cols];
                    for t in 0..n_frames {
                        let base = t * self.n_groups * 3;
                        let sample = &self.series[base..base + self.n_groups * 3];
                        let axis = self.axis;
                        let type_ids = &self.type_ids;
                        let type_counts = &self.type_counts;
                        let n_groups = self.n_groups;
                        let dt_dec = self.dt_decimation;
                        let acc_ref = &mut acc;
                        let lags_ref = &lags;
                        buffer.update(sample, |lag_idx, cur, old| {
                            let lag = lags_ref[lag_idx];
                            if !lag_allowed(lag, dt_dec) {
                                return;
                            }
                            accumulate_msd(
                                acc_ref,
                                lag_idx,
                                cols,
                                axis,
                                n_groups,
                                type_ids,
                                type_counts,
                                cur,
                                old,
                            );
                        });
                    }
                    let counts = buffer.n_pairs().to_vec();
                    let mut time = Vec::with_capacity(lags.len());
                    let mut data = vec![0.0f32; lags.len() * cols];
                    for (idx, &lag) in lags.iter().enumerate() {
                        time.push((dt0 * lag as f64) as f32);
                        let count = counts.get(idx).copied().unwrap_or(0) as f64;
                        if count == 0.0 {
                            continue;
                        }
                        let base = idx * cols;
                        for c in 0..cols {
                            data[base + c] = (acc[base + c] / count) as f32;
                        }
                    }
                    return Ok(PlanOutput::TimeSeries {
                        time,
                        data,
                        rows: lags.len(),
                        cols,
                    });
                }

                let (lags, acc, counts) = msd_fft(
                    &self.series,
                    n_frames,
                    self.n_groups,
                    &self.type_ids,
                    &self.type_counts,
                    self.axis,
                    self.dt_decimation,
                )?;
                let mut time = Vec::with_capacity(lags.len());
                let mut data = vec![0.0f32; lags.len() * cols];
                for (idx, &lag) in lags.iter().enumerate() {
                    time.push((dt0 * lag as f64) as f32);
                    let count = counts[idx] as f64;
                    if count == 0.0 {
                        continue;
                    }
                    let base = idx * cols;
                    for c in 0..cols {
                        data[base + c] = (acc[base + c] / count) as f32;
                    }
                }
                Ok(PlanOutput::TimeSeries {
                    time,
                    data,
                    rows: lags.len(),
                    cols,
                })
            }
            LagMode::Ring => {
                let counts = self
                    .ring
                    .as_ref()
                    .map(|r| r.n_pairs().to_vec())
                    .unwrap_or_default();
                let mut time = Vec::with_capacity(self.lags.len());
                let mut data = vec![0.0f32; self.lags.len() * cols];
                for (idx, &lag) in self.lags.iter().enumerate() {
                    time.push((dt0 * lag as f64) as f32);
                    let count = counts.get(lag).copied().unwrap_or(0) as f64;
                    if count == 0.0 {
                        continue;
                    }
                    let base = idx * cols;
                    for c in 0..cols {
                        data[base + c] = (self.acc[base + c] / count) as f32;
                    }
                }
                Ok(PlanOutput::TimeSeries {
                    time,
                    data,
                    rows: self.lags.len(),
                    cols,
                })
            }
            LagMode::MultiTau => {
                let counts = self
                    .multi_tau
                    .as_ref()
                    .map(|m| m.n_pairs().to_vec())
                    .unwrap_or_default();
                let mut time = Vec::with_capacity(self.lags.len());
                let mut data = vec![0.0f32; self.lags.len() * cols];
                for (idx, &lag) in self.lags.iter().enumerate() {
                    time.push((dt0 * lag as f64) as f32);
                    let count = counts.get(idx).copied().unwrap_or(0) as f64;
                    if count == 0.0 {
                        continue;
                    }
                    let base = idx * cols;
                    for c in 0..cols {
                        data[base + c] = (self.acc[base + c] / count) as f32;
                    }
                }
                Ok(PlanOutput::TimeSeries {
                    time,
                    data,
                    rows: self.lags.len(),
                    cols,
                })
            }
            LagMode::Auto => Ok(PlanOutput::TimeSeries {
                time: Vec::new(),
                data: Vec::new(),
                rows: 0,
                cols: 0,
            }),
        }
    }
}

fn msd_cols(axis: Option<[f64; 3]>, n_types: usize) -> usize {
    let components = if axis.is_some() { 5 } else { 4 };
    components * (n_types + 1)
}

fn lag_allowed(lag: usize, dec: Option<DtDecimation>) -> bool {
    if let Some(dec) = dec {
        if lag > dec.cut2 && (lag % dec.stride2) != 0 {
            return false;
        }
        if lag > dec.cut1 && (lag % dec.stride1) != 0 {
            return false;
        }
    }
    true
}

fn accumulate_msd(
    acc: &mut [f64],
    lag_idx: usize,
    cols: usize,
    axis: Option<[f64; 3]>,
    n_groups: usize,
    type_ids: &[usize],
    type_counts: &[usize],
    cur: &[f32],
    old: &[f32],
) {
    let n_types = type_counts.len();
    let n_groups_f = n_groups as f64;
    let base = lag_idx * cols;
    let block = n_types + 1;
    for g in 0..n_groups {
        let idx = g * 3;
        let dx = (cur[idx] - old[idx]) as f64;
        let dy = (cur[idx + 1] - old[idx + 1]) as f64;
        let dz = (cur[idx + 2] - old[idx + 2]) as f64;
        let msd_x = dx * dx;
        let msd_y = dy * dy;
        let msd_z = dz * dz;
        let msd_tot = msd_x + msd_y + msd_z;
        let msd_axis = axis.map(|a| {
            let proj = dx * a[0] + dy * a[1] + dz * a[2];
            proj * proj
        });
        let type_id = type_ids[g];
        let type_count = type_counts[type_id] as f64;
        let mut offset = base + type_id;
        acc[offset] += msd_x / type_count;
        acc[offset + block] += msd_y / type_count;
        acc[offset + 2 * block] += msd_z / type_count;
        if let Some(axis_val) = msd_axis {
            acc[offset + 3 * block] += axis_val / type_count;
            acc[offset + 4 * block] += msd_tot / type_count;
        } else {
            acc[offset + 3 * block] += msd_tot / type_count;
        }

        offset = base + n_types;
        acc[offset] += msd_x / n_groups_f;
        acc[offset + block] += msd_y / n_groups_f;
        acc[offset + 2 * block] += msd_z / n_groups_f;
        if let Some(axis_val) = msd_axis {
            acc[offset + 3 * block] += axis_val / n_groups_f;
            acc[offset + 4 * block] += msd_tot / n_groups_f;
        } else {
            acc[offset + 3 * block] += msd_tot / n_groups_f;
        }
    }
}

fn msd_fft(
    series: &[f32],
    n_frames: usize,
    n_groups: usize,
    type_ids: &[usize],
    type_counts: &[usize],
    axis: Option<[f64; 3]>,
    dt_decimation: Option<DtDecimation>,
) -> TrajResult<(Vec<usize>, Vec<f64>, Vec<u64>)> {
    let n_types = type_counts.len();
    let cols = msd_cols(axis, n_types);
    let mut lags = Vec::with_capacity(n_frames - 1);
    for lag in 1..n_frames {
        if lag_allowed(lag, dt_decimation) {
            lags.push(lag);
        }
    }

    if lags.is_empty() {
        return Ok((Vec::new(), Vec::new(), Vec::new()));
    }

    let mut acc = vec![0.0f64; lags.len() * cols];
    let mut counts = vec![0u64; lags.len()];
    for (idx, &lag) in lags.iter().enumerate() {
        counts[idx] = (n_frames - lag) as u64;
    }

    let n_groups_f = n_groups as f64;
    for g in 0..n_groups {
        let mut x = vec![0.0f32; n_frames];
        let mut y = vec![0.0f32; n_frames];
        let mut z = vec![0.0f32; n_frames];
        for t in 0..n_frames {
            let base = t * n_groups * 3 + g * 3;
            x[t] = series[base];
            y[t] = series[base + 1];
            z[t] = series[base + 2];
        }
        let (msd_x, msd_y, msd_z, msd_axis) = msd_fft_series(&x, &y, &z, axis)?;
        let type_id = type_ids[g];
        let type_count = type_counts[type_id] as f64;
        for (out_idx, &lag) in lags.iter().enumerate() {
            let idx = lag - 1;
            let base = out_idx * cols;
            let block = n_types + 1;
            let mut offset = base + type_id;
            acc[offset] += msd_x[idx] / type_count;
            acc[offset + block] += msd_y[idx] / type_count;
            acc[offset + 2 * block] += msd_z[idx] / type_count;
            if let Some(ref axis_vals) = msd_axis {
                acc[offset + 3 * block] += axis_vals[idx] / type_count;
                acc[offset + 4 * block] += (msd_x[idx] + msd_y[idx] + msd_z[idx]) / type_count;
            } else {
                acc[offset + 3 * block] += (msd_x[idx] + msd_y[idx] + msd_z[idx]) / type_count;
            }

            offset = base + n_types;
            acc[offset] += msd_x[idx] / n_groups_f;
            acc[offset + block] += msd_y[idx] / n_groups_f;
            acc[offset + 2 * block] += msd_z[idx] / n_groups_f;
            if let Some(ref axis_vals) = msd_axis {
                acc[offset + 3 * block] += axis_vals[idx] / n_groups_f;
                acc[offset + 4 * block] += (msd_x[idx] + msd_y[idx] + msd_z[idx]) / n_groups_f;
            } else {
                acc[offset + 3 * block] += (msd_x[idx] + msd_y[idx] + msd_z[idx]) / n_groups_f;
            }
        }
    }

    Ok((lags, acc, counts))
}

fn msd_fft_series(
    x: &[f32],
    y: &[f32],
    z: &[f32],
    axis: Option<[f64; 3]>,
) -> TrajResult<(Vec<f64>, Vec<f64>, Vec<f64>, Option<Vec<f64>>)> {
    let msd_x = msd_from_series(x)?;
    let msd_y = msd_from_series(y)?;
    let msd_z = msd_from_series(z)?;
    let msd_axis = if let Some(a) = axis {
        let mut p = vec![0.0f32; x.len()];
        for i in 0..x.len() {
            p[i] = (x[i] as f64 * a[0] + y[i] as f64 * a[1] + z[i] as f64 * a[2]) as f32;
        }
        Some(msd_from_series(&p)?)
    } else {
        None
    };
    Ok((msd_x, msd_y, msd_z, msd_axis))
}

fn msd_from_series(series: &[f32]) -> TrajResult<Vec<f64>> {
    let n = series.len();
    if n < 2 {
        return Ok(Vec::new());
    }
    let mut r2 = vec![0.0f64; n + 1];
    for i in 0..n {
        r2[i + 1] = r2[i] + (series[i] as f64) * (series[i] as f64);
    }
    let ac = autocorr_real(series)?;
    let mut msd = vec![0.0f64; n - 1];
    for lag in 1..n {
        let count = (n - lag) as f64;
        let sum1 = r2[n - lag];
        let sum2 = r2[n] - r2[lag];
        let val = (sum1 + sum2 - 2.0 * ac[lag] as f64) / count;
        msd[lag - 1] = val;
    }
    Ok(msd)
}

fn autocorr_real(series: &[f32]) -> TrajResult<Vec<f32>> {
    use rustfft::num_complex::Complex;
    use rustfft::FftPlanner;

    let n = series.len();
    let size = (n * 2).next_power_of_two();
    let mut planner = FftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(size);
    let ifft = planner.plan_fft_inverse(size);
    let mut buf = vec![Complex { re: 0.0f32, im: 0.0f32 }; size];
    for i in 0..n {
        buf[i].re = series[i];
    }
    fft.process(&mut buf);
    for v in &mut buf {
        let re = v.re;
        let im = v.im;
        v.re = re * re + im * im;
        v.im = 0.0;
    }
    ifft.process(&mut buf);
    let scale = 1.0 / size as f32;
    let mut out = vec![0.0f32; n];
    for i in 0..n {
        out[i] = buf[i].re * scale;
    }
    Ok(out)
}

fn box_lengths(box_: &Box3) -> Option<[f64; 3]> {
    match box_ {
        Box3::Orthorhombic { lx, ly, lz } => Some([*lx as f64, *ly as f64, *lz as f64]),
        Box3::Triclinic { .. } => None,
        Box3::None => None,
    }
}
