use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::{Box3, FrameChunk};
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::correlators::{LagMode, LagSettings};
use crate::correlators::multi_tau::MultiTauBuffer;
use crate::correlators::ring::RingBuffer;
use crate::executor::{Device, Plan, PlanOutput};
#[cfg(feature = "cuda")]
use crate::plans::analysis::common::groups_to_csr;
use crate::plans::analysis::grouping::{GroupBy, GroupMap, GroupSpec};
use crate::plans::analysis::msd::{DtDecimation, FrameDecimation, TimeBinning};

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuBufferF32, GpuContext, GpuGroups};

pub struct ConductivityPlan {
    selection: Selection,
    group_by: GroupBy,
    group_types: Option<Vec<usize>>,
    charges: Vec<f64>,
    temperature: f64,
    transference: bool,
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
    group_charge: Vec<f64>,
    dt0: Option<f64>,
    uniform_time: bool,
    last_time: Option<f64>,
    frame_index: usize,
    samples_seen: usize,
    vol_sum: f64,
    vol_count: usize,
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
    fft_store_groups: bool,
    #[cfg(feature = "cuda")]
    gpu: Option<ConductivityGpuState>,
}

#[cfg(feature = "cuda")]
struct ConductivityGpuState {
    ctx: GpuContext,
    groups: GpuGroups,
    masses: GpuBufferF32,
}

impl ConductivityPlan {
    pub fn new(selection: Selection, group_by: GroupBy, charges: Vec<f64>, temperature: f64) -> Self {
        Self {
            selection,
            group_by,
            group_types: None,
            charges,
            temperature,
            transference: false,
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
            group_charge: Vec::new(),
            dt0: None,
            uniform_time: true,
            last_time: None,
            frame_index: 0,
            samples_seen: 0,
            vol_sum: 0.0,
            vol_count: 0,
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
            fft_store_groups: false,
            #[cfg(feature = "cuda")]
            gpu: None,
        }
    }

    pub fn with_transference(mut self, enabled: bool) -> Self {
        self.transference = enabled;
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

impl Plan for ConductivityPlan {
    fn name(&self) -> &'static str {
        "conductivity"
    }

    fn set_frames_hint(&mut self, n_frames: Option<usize>) {
        self.frames_hint = n_frames;
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        self.n_atoms = system.n_atoms();
        if self.charges.len() != self.n_atoms {
            return Err(TrajError::Mismatch(
                "charges length does not match atom count".into(),
            ));
        }
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
        self.group_charge = vec![0.0f64; self.n_groups];
        for (g_idx, atoms) in self.groups.as_ref().unwrap().groups.iter().enumerate() {
            let mut sum = 0.0f64;
            for &atom_idx in atoms {
                sum += self.charges[atom_idx];
            }
            self.group_charge[g_idx] = sum;
        }

        self.dt0 = None;
        self.uniform_time = true;
        self.last_time = None;
        self.frame_index = 0;
        self.samples_seen = 0;
        self.vol_sum = 0.0;
        self.vol_count = 0;
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

        #[cfg(feature = "cuda")]
        {
            self.gpu = None;
            if let Device::Cuda(ctx) = device {
                let (offsets, indices, max_len) = groups_to_csr(&self.groups.as_ref().unwrap().groups);
                let groups = ctx.groups(&offsets, &indices, max_len)?;
                let masses: Vec<f32> = system.atoms.mass.iter().map(|m| *m).collect();
                let masses = ctx.upload_f32(&masses)?;
                self.gpu = Some(ConductivityGpuState {
                    ctx: ctx.clone(),
                    groups,
                    masses,
                });
            }
        }
        #[cfg(not(feature = "cuda"))]
        let _ = device;

        let has_gpu = {
            #[cfg(feature = "cuda")]
            {
                self.gpu.is_some()
            }
            #[cfg(not(feature = "cuda"))]
            {
                false
            }
        };

        let n_types = self.type_counts.len();
        let fft_streams = if self.transference { n_types + 1 } else { 1 };
        let mut resolved_mode = self.lag.mode;
        if resolved_mode == LagMode::Auto {
            let use_fft = if let Some(n_frames) = self.frames_hint {
                self.lag.fft_fits(n_frames, fft_streams, 3, 4)
            } else {
                false
            };
            resolved_mode = if use_fft { LagMode::Fft } else { LagMode::MultiTau };
        }
        self.resolved_mode = resolved_mode;
        self.fft_store_groups = false;

        let cols = if self.transference {
            n_types * n_types + 1
        } else {
            1
        };

        match self.resolved_mode {
            LagMode::MultiTau => {
                let buffer = MultiTauBuffer::new(self.n_groups, 3, self.lag.multi_tau_m, self.lag.multi_tau_max_levels);
                self.lags = buffer.out_lags().to_vec();
                self.acc = vec![0.0f64; self.lags.len() * cols];
                self.multi_tau = Some(buffer);
            }
            LagMode::Ring => {
                let max_lag = self.lag.ring_max_lag_capped(self.n_groups, 3, 4);
                let buffer = RingBuffer::new(self.n_groups, 3, max_lag);
                self.lags = (1..=max_lag).collect();
                self.acc = vec![0.0f64; self.lags.len() * cols];
                self.ring = Some(buffer);
            }
            LagMode::Fft => {
                if has_gpu {
                    self.fft_store_groups = true;
                    let capacity = self
                        .frames_hint
                        .unwrap_or(0)
                        .saturating_mul(self.n_groups)
                        .saturating_mul(3);
                    self.series = Vec::with_capacity(capacity);
                } else {
                    let capacity = self
                        .frames_hint
                        .unwrap_or(0)
                        .saturating_mul(fft_streams)
                        .saturating_mul(3);
                    self.series = Vec::with_capacity(capacity);
                }
            }
            LagMode::Auto => {}
        }

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

            if let Some(b) = box_lengths(&chunk.box_[frame]) {
                let vol = b[0] * b[1] * b[2] * self.length_scale.powi(3);
                self.vol_sum += vol;
                self.vol_count += 1;
            }

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
                        let dt_dec = self.dt_decimation;
                        let lags = &self.lags;
                        let acc = &mut self.acc;
                        let type_ids = &self.type_ids;
                        let n_types = self.type_counts.len();
                        let n_groups = self.n_groups;
                        let transference = self.transference;
                        let group_charge = &self.group_charge;
                        buffer.update(&self.sample_f32, |lag_idx, cur, old| {
                            let lag = lags[lag_idx];
                            if !lag_allowed(lag, dt_dec) {
                                return;
                            }
                            accumulate_conductivity(
                                acc,
                                lag_idx,
                                n_groups,
                                n_types,
                                type_ids,
                                group_charge,
                                transference,
                                cur,
                                old,
                            );
                        });
                    }
                }
                LagMode::Ring => {
                    if let Some(buffer) = &mut self.ring {
                        let dt_dec = self.dt_decimation;
                        let acc = &mut self.acc;
                        let type_ids = &self.type_ids;
                        let n_types = self.type_counts.len();
                        let n_groups = self.n_groups;
                        let transference = self.transference;
                        let group_charge = &self.group_charge;
                        buffer.update(&self.sample_f32, |lag, cur, old| {
                            if !lag_allowed(lag, dt_dec) {
                                return;
                            }
                            let lag_idx = lag - 1;
                            accumulate_conductivity(
                                acc,
                                lag_idx,
                                n_groups,
                                n_types,
                                type_ids,
                                group_charge,
                                transference,
                                cur,
                                old,
                            );
                        });
                    }
                }
                LagMode::Fft => {
                    if self.fft_store_groups {
                        self.series.extend_from_slice(&self.sample_f32);
                    } else {
                        let n_types = self.type_counts.len();
                        let streams = if self.transference { n_types + 1 } else { 1 };
                        let mut sums = vec![[0.0f64; 3]; streams];
                        for g in 0..self.n_groups {
                            let q = self.group_charge[g];
                            let base = g * 3;
                            let vec = [
                                self.sample_f32[base] as f64 * q,
                                self.sample_f32[base + 1] as f64 * q,
                                self.sample_f32[base + 2] as f64 * q,
                            ];
                            let t = if self.transference { self.type_ids[g] } else { 0 };
                            sums[t][0] += vec[0];
                            sums[t][1] += vec[1];
                            sums[t][2] += vec[2];
                            if self.transference {
                                let total = n_types;
                                sums[total][0] += vec[0];
                                sums[total][1] += vec[1];
                                sums[total][2] += vec[2];
                            }
                        }
                        for s in 0..streams {
                            self.series.push(sums[s][0] as f32);
                            self.series.push(sums[s][1] as f32);
                            self.series.push(sums[s][2] as f32);
                        }
                    }
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
                let n_types = self.type_counts.len();
                let streams = if self.transference { n_types + 1 } else { 1 };
                self.series.len() / (streams * 3)
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

        let volavg = average_volume(self.vol_sum, self.vol_count)?;
        let kb = 1.380648813e-23_f64;
        let qelec = 1.60217656535e-19_f64;
        let multi = qelec * qelec / (6.0 * kb * self.temperature * volavg);
        let dt0 = self.dt0.unwrap_or(1.0);
        let n_types = self.type_counts.len();
        let cols = if self.transference {
            n_types * n_types + 1
        } else {
            1
        };

        match self.resolved_mode {
            LagMode::Fft => {
                if self.uniform_time && self.fft_store_groups {
                    #[cfg(feature = "cuda")]
                    if let Some(gpu) = &self.gpu {
                        let ndframe = n_frames.saturating_sub(1);
                        if ndframe > 0 {
                            let times_f32: Vec<f32> = (0..n_frames)
                                .map(|i| (dt0 * i as f64) as f32)
                                .collect();
                            let group_charge_f32: Vec<f32> = self
                                .group_charge
                                .iter()
                                .map(|q| *q as f32)
                                .collect();
                            let type_ids_u32: Vec<u32> =
                                self.type_ids.iter().map(|t| *t as u32).collect();
                            let mut type_charge_f32 = vec![0.0f32; n_types];
                            for (g_idx, &t) in self.type_ids.iter().enumerate() {
                                type_charge_f32[t] += self.group_charge[g_idx] as f32;
                            }
                            let time_binning = (
                                self.time_binning.eps_num as f32,
                                self.time_binning.eps_add as f32,
                            );
                            let (out_gpu, n_diff_gpu, cols_gpu) = gpu.ctx.conductivity_time_lag(
                                &self.series,
                                &times_f32,
                                &group_charge_f32,
                                &type_ids_u32,
                                &type_charge_f32,
                                self.n_groups,
                                n_types,
                                ndframe,
                                self.transference,
                                None,
                                self.dt_decimation.map(|d| (d.cut1, d.stride1, d.cut2, d.stride2)),
                                time_binning,
                            )?;
                            if cols_gpu == cols && !out_gpu.is_empty() {
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
                                            (out_gpu[base + c] as f64 * multi / count) as f32;
                                    }
                                }
                                if self.transference {
                                    for i in 0..n_types {
                                        for j in 0..i {
                                            let idx = j + i * n_types;
                                            let idx2 = i + j * n_types;
                                            for row in 0..lags.len() {
                                                let base = row * cols;
                                                let val = 0.5 * data[base + idx];
                                                data[base + idx] = val;
                                                data[base + idx2] = val;
                                            }
                                        }
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
                    if self.fft_store_groups {
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
                            let dt_dec = self.dt_decimation;
                            let lags_ref = &lags;
                            let acc_ref = &mut acc;
                            let transference = self.transference;
                            let type_ids = &self.type_ids;
                            let group_charge = &self.group_charge;
                            buffer.update(sample, |lag_idx, cur, old| {
                                let lag = lags_ref[lag_idx];
                                if !lag_allowed(lag, dt_dec) {
                                    return;
                                }
                                accumulate_conductivity(
                                    acc_ref,
                                    lag_idx,
                                    self.n_groups,
                                    n_types,
                                    type_ids,
                                    group_charge,
                                    transference,
                                    cur,
                                    old,
                                );
                            });
                        }
                        let counts = buffer.n_pairs().to_vec();
                        return Ok(build_conductivity_output(
                            &lags,
                            &acc,
                            &counts,
                            dt0,
                            cols,
                            multi,
                        ));
                    } else {
                        let streams = if self.transference { n_types + 1 } else { 1 };
                        let mut buffer = MultiTauBuffer::new(
                            streams,
                            3,
                            self.lag.multi_tau_m,
                            self.lag.multi_tau_max_levels,
                        );
                        let lags = buffer.out_lags().to_vec();
                        let mut acc = vec![0.0f64; lags.len() * cols];
                        for t in 0..n_frames {
                            let base = t * streams * 3;
                            let sample = &self.series[base..base + streams * 3];
                            let dt_dec = self.dt_decimation;
                            let lags_ref = &lags;
                            let acc_ref = &mut acc;
                            let transference = self.transference;
                            buffer.update(sample, |lag_idx, cur, old| {
                                let lag = lags_ref[lag_idx];
                                if !lag_allowed(lag, dt_dec) {
                                    return;
                                }
                                accumulate_conductivity_streams(
                                    acc_ref,
                                    lag_idx,
                                    n_types,
                                    transference,
                                    cur,
                                    old,
                                );
                            });
                        }
                        let counts = buffer.n_pairs().to_vec();
                        return Ok(build_conductivity_output(
                            &lags,
                            &acc,
                            &counts,
                            dt0,
                            cols,
                            multi,
                        ));
                    }
                }

                let (lags, acc, counts) = conductivity_fft(
                    &self.series,
                    n_frames,
                    n_types,
                    self.transference,
                    self.dt_decimation,
                )?;
                Ok(build_conductivity_output(
                    &lags,
                    &acc,
                    &counts,
                    dt0,
                    cols,
                    multi,
                ))
            }
            LagMode::Ring => {
                let counts = self
                    .ring
                    .as_ref()
                    .map(|r| r.n_pairs().to_vec())
                    .unwrap_or_default();
                Ok(build_conductivity_output(
                    &self.lags,
                    &self.acc,
                    &counts,
                    dt0,
                    cols,
                    multi,
                ))
            }
            LagMode::MultiTau => {
                let counts = self
                    .multi_tau
                    .as_ref()
                    .map(|m| m.n_pairs().to_vec())
                    .unwrap_or_default();
                Ok(build_conductivity_output(
                    &self.lags,
                    &self.acc,
                    &counts,
                    dt0,
                    cols,
                    multi,
                ))
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

fn accumulate_conductivity(
    acc: &mut [f64],
    lag_idx: usize,
    n_groups: usize,
    n_types: usize,
    type_ids: &[usize],
    group_charge: &[f64],
    transference: bool,
    cur: &[f32],
    old: &[f32],
) {
    let cols = if transference { n_types * n_types + 1 } else { 1 };
    let base = lag_idx * cols;
    let mut sum_all = [0.0f64; 3];
    let mut sum_type = vec![[0.0f64; 3]; n_types];
    for g in 0..n_groups {
        let idx = g * 3;
        let q = group_charge[g];
        let dx = (cur[idx] - old[idx]) as f64 * q;
        let dy = (cur[idx + 1] - old[idx + 1]) as f64 * q;
        let dz = (cur[idx + 2] - old[idx + 2]) as f64 * q;
        sum_all[0] += dx;
        sum_all[1] += dy;
        sum_all[2] += dz;
        if transference {
            let t = type_ids[g];
            sum_type[t][0] += dx;
            sum_type[t][1] += dy;
            sum_type[t][2] += dz;
        }
    }

    if transference {
        for i in 0..n_types {
            let v1 = sum_type[i];
            let dot = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2];
            acc[base + i + i * n_types] += dot;
            for j in (i + 1)..n_types {
                let v2 = sum_type[j];
                let dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
                acc[base + j + i * n_types] += dot;
                acc[base + i + j * n_types] += dot;
            }
        }
    }

    let dot = sum_all[0] * sum_all[0] + sum_all[1] * sum_all[1] + sum_all[2] * sum_all[2];
    acc[base + (cols - 1)] += dot;
}

fn accumulate_conductivity_streams(
    acc: &mut [f64],
    lag_idx: usize,
    n_types: usize,
    transference: bool,
    cur: &[f32],
    old: &[f32],
) {
    let streams = if transference { n_types + 1 } else { 1 };
    let cols = if transference { n_types * n_types + 1 } else { 1 };
    let base = lag_idx * cols;
    let mut dvecs = vec![[0.0f64; 3]; streams];
    for s in 0..streams {
        let idx = s * 3;
        dvecs[s][0] = (cur[idx] - old[idx]) as f64;
        dvecs[s][1] = (cur[idx + 1] - old[idx + 1]) as f64;
        dvecs[s][2] = (cur[idx + 2] - old[idx + 2]) as f64;
    }
    if transference {
        for i in 0..n_types {
            let v1 = dvecs[i];
            let dot = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2];
            acc[base + i + i * n_types] += dot;
            for j in (i + 1)..n_types {
                let v2 = dvecs[j];
                let dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
                acc[base + j + i * n_types] += dot;
                acc[base + i + j * n_types] += dot;
            }
        }
        let total = dvecs[n_types];
        let dot = total[0] * total[0] + total[1] * total[1] + total[2] * total[2];
        acc[base + cols - 1] += dot;
    } else {
        let v = dvecs[0];
        acc[base] += v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
    }
}

fn build_conductivity_output(
    lags: &[usize],
    acc: &[f64],
    counts: &[u64],
    dt0: f64,
    cols: usize,
    multi: f64,
) -> PlanOutput {
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
            data[base + c] = (acc[base + c] * multi / count) as f32;
        }
    }

    PlanOutput::TimeSeries {
        time,
        data,
        rows: lags.len(),
        cols,
    }
}

fn conductivity_fft(
    series: &[f32],
    n_frames: usize,
    n_types: usize,
    transference: bool,
    dt_decimation: Option<DtDecimation>,
) -> TrajResult<(Vec<usize>, Vec<f64>, Vec<u64>)> {
    let streams = if transference { n_types + 1 } else { 1 };
    let cols = if transference { n_types * n_types + 1 } else { 1 };
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

    let mut comps = vec![vec![vec![0.0f32; n_frames]; 3]; streams];
    for t in 0..n_frames {
        for s in 0..streams {
            let base = (t * streams + s) * 3;
            comps[s][0][t] = series[base];
            comps[s][1][t] = series[base + 1];
            comps[s][2][t] = series[base + 2];
        }
    }

    let compute_pair = |i: usize, j: usize| -> TrajResult<Vec<f64>> {
        let mut dot_series = vec![0.0f64; n_frames];
        for t in 0..n_frames {
            dot_series[t] = comps[i][0][t] as f64 * comps[j][0][t] as f64
                + comps[i][1][t] as f64 * comps[j][1][t] as f64
                + comps[i][2][t] as f64 * comps[j][2][t] as f64;
        }
        let mut prefix = vec![0.0f64; n_frames + 1];
        for t in 0..n_frames {
            prefix[t + 1] = prefix[t] + dot_series[t];
        }
        let xcorr_x = xcorr_real(&comps[i][0], &comps[j][0])?;
        let xcorr_y = xcorr_real(&comps[i][1], &comps[j][1])?;
        let xcorr_z = xcorr_real(&comps[i][2], &comps[j][2])?;
        let (xcorr_rx, xcorr_ry, xcorr_rz) = if i == j {
            (xcorr_x.clone(), xcorr_y.clone(), xcorr_z.clone())
        } else {
            (
                xcorr_real(&comps[j][0], &comps[i][0])?,
                xcorr_real(&comps[j][1], &comps[i][1])?,
                xcorr_real(&comps[j][2], &comps[i][2])?,
            )
        };
        let mut sums = vec![0.0f64; lags.len()];
        for (idx, &lag) in lags.iter().enumerate() {
            let sum1 = prefix[n_frames - lag];
            let sum2 = prefix[n_frames] - prefix[lag];
            let cross = xcorr_x[lag] as f64 + xcorr_y[lag] as f64 + xcorr_z[lag] as f64;
            let cross_r = xcorr_rx[lag] as f64 + xcorr_ry[lag] as f64 + xcorr_rz[lag] as f64;
            sums[idx] = sum1 + sum2 - cross - cross_r;
        }
        Ok(sums)
    };

    if transference {
        for i in 0..n_types {
            for j in i..n_types {
                let sums = compute_pair(i, j)?;
                for (idx, sum_val) in sums.into_iter().enumerate() {
                    let base = idx * cols;
                    acc[base + j + i * n_types] += sum_val;
                    if i != j {
                        acc[base + i + j * n_types] += sum_val;
                    }
                }
            }
        }
        let total = n_types;
        let sums = compute_pair(total, total)?;
        for (idx, sum_val) in sums.into_iter().enumerate() {
            let base = idx * cols;
            acc[base + cols - 1] += sum_val;
        }
    } else {
        let sums = compute_pair(0, 0)?;
        for (idx, sum_val) in sums.into_iter().enumerate() {
            let base = idx * cols;
            acc[base] += sum_val;
        }
    }

    Ok((lags, acc, counts))
}

fn xcorr_real(a: &[f32], b: &[f32]) -> TrajResult<Vec<f32>> {
    use rustfft::num_complex::Complex;
    use rustfft::FftPlanner;

    let n = a.len();
    let size = (n * 2).next_power_of_two();
    let mut planner = FftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(size);
    let ifft = planner.plan_fft_inverse(size);
    let mut buf_a = vec![Complex { re: 0.0f32, im: 0.0f32 }; size];
    let mut buf_b = vec![Complex { re: 0.0f32, im: 0.0f32 }; size];
    for i in 0..n {
        buf_a[i].re = a[i];
        buf_b[i].re = b[i];
    }
    fft.process(&mut buf_a);
    fft.process(&mut buf_b);
    for i in 0..size {
        let ar = buf_a[i].re;
        let ai = buf_a[i].im;
        let br = buf_b[i].re;
        let bi = buf_b[i].im;
        buf_a[i].re = ar * br + ai * bi;
        buf_a[i].im = ar * bi - ai * br;
    }
    ifft.process(&mut buf_a);
    let scale = 1.0 / size as f32;
    let mut out = vec![0.0f32; n];
    for i in 0..n {
        out[i] = buf_a[i].re * scale;
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

fn average_volume(sum: f64, count: usize) -> TrajResult<f64> {
    if count == 0 {
        return Err(TrajError::Mismatch(
            "conductivity requires orthorhombic box".into(),
        ));
    }
    let vol_nm3 = sum / (count as f64);
    Ok(vol_nm3 * 1.0e-27)
}
