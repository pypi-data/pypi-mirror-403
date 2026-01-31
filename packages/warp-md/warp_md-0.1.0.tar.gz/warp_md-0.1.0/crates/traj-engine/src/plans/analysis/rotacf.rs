use std::collections::HashSet;

use traj_core::error::{TrajError, TrajResult};
use traj_core::frame::FrameChunk;
use traj_core::selection::Selection;
use traj_core::system::System;

use crate::correlators::{LagMode, LagSettings};
use crate::correlators::multi_tau::MultiTauBuffer;
use crate::correlators::ring::RingBuffer;
use crate::executor::{Device, Plan, PlanOutput};
use crate::plans::analysis::grouping::{GroupBy, GroupMap, GroupSpec};
use crate::plans::analysis::msd::{DtDecimation, FrameDecimation, TimeBinning};
#[cfg(feature = "cuda")]
use crate::plans::analysis::common::anchors_to_u32;

#[cfg(feature = "cuda")]
use traj_gpu::{convert_coords, GpuAnchors, GpuContext};

#[derive(Clone)]
pub enum OrientationSpec {
    PlaneIndices([usize; 3]),
    VectorIndices([usize; 2]),
    PlaneSelections([Selection; 3]),
    VectorSelections([Selection; 2]),
}

#[derive(Clone, Copy)]
enum OrientationKind {
    Plane,
    Vector,
}

pub struct RotAcfPlan {
    selection: Selection,
    group_by: GroupBy,
    group_types: Option<Vec<usize>>,
    orientation: OrientationSpec,
    orientation_kind: OrientationKind,
    length_scale: f64,
    frame_decimation: Option<FrameDecimation>,
    dt_decimation: Option<DtDecimation>,
    time_binning: TimeBinning,
    p2_legendre: bool,
    lag: LagSettings,
    frames_hint: Option<usize>,
    resolved_mode: LagMode,
    groups: Option<GroupMap>,
    anchors: Option<Vec<[usize; 3]>>,
    type_ids: Vec<usize>,
    type_counts: Vec<usize>,
    n_groups: usize,
    dt0: Option<f64>,
    uniform_time: bool,
    last_time: Option<f64>,
    frame_index: usize,
    samples_seen: usize,
    sample_f32: Vec<f32>,
    lags: Vec<usize>,
    acc: Vec<f64>,
    multi_tau: Option<MultiTauBuffer>,
    ring: Option<RingBuffer>,
    series: Vec<f32>,
    #[cfg(feature = "cuda")]
    gpu: Option<RotAcfGpuState>,
}

#[cfg(feature = "cuda")]
struct RotAcfGpuState {
    ctx: GpuContext,
    anchors: GpuAnchors,
    kind: OrientationKind,
}

impl RotAcfPlan {
    pub fn new(selection: Selection, group_by: GroupBy, orientation: OrientationSpec) -> Self {
        let kind = match orientation {
            OrientationSpec::PlaneIndices(_) | OrientationSpec::PlaneSelections(_) => {
                OrientationKind::Plane
            }
            OrientationSpec::VectorIndices(_) | OrientationSpec::VectorSelections(_) => {
                OrientationKind::Vector
            }
        };
        Self {
            selection,
            group_by,
            group_types: None,
            orientation,
            orientation_kind: kind,
            length_scale: 1.0,
            frame_decimation: None,
            dt_decimation: None,
            time_binning: TimeBinning::default(),
            p2_legendre: true,
            lag: LagSettings::default(),
            frames_hint: None,
            resolved_mode: LagMode::Auto,
            groups: None,
            anchors: None,
            type_ids: Vec::new(),
            type_counts: Vec::new(),
            n_groups: 0,
            dt0: None,
            uniform_time: true,
            last_time: None,
            frame_index: 0,
            samples_seen: 0,
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

    pub fn with_p2_legendre(mut self, enabled: bool) -> Self {
        self.p2_legendre = enabled;
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

impl Plan for RotAcfPlan {
    fn name(&self) -> &'static str {
        "rotacf"
    }

    fn set_frames_hint(&mut self, n_frames: Option<usize>) {
        self.frames_hint = n_frames;
    }

    fn init(&mut self, system: &System, device: &Device) -> TrajResult<()> {
        let mut spec = GroupSpec::new(self.selection.clone(), self.group_by);
        if let Some(types) = &self.group_types {
            spec = spec.with_group_types(types.clone());
        }
        let groups = spec.build(system)?;
        let anchors = resolve_orientation(&self.orientation, &groups, system)?;
        self.n_groups = groups.n_groups();
        self.type_ids = groups.type_ids();
        self.type_counts = groups.type_counts();
        self.groups = Some(groups);
        self.anchors = Some(anchors);

        self.dt0 = None;
        self.uniform_time = true;
        self.last_time = None;
        self.frame_index = 0;
        self.samples_seen = 0;
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
                let cols = 2 * (self.type_counts.len() + 1);
                self.acc = vec![0.0f64; self.lags.len() * cols];
                self.multi_tau = Some(buffer);
            }
            LagMode::Ring => {
                let max_lag = self.lag.ring_max_lag_capped(self.n_groups, 3, 4);
                let buffer = RingBuffer::new(self.n_groups, 3, max_lag);
                self.lags = (1..=max_lag).collect();
                let cols = 2 * (self.type_counts.len() + 1);
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
                let anchors_u32 = anchors_to_u32(self.anchors.as_ref().unwrap());
                let anchors_gpu = ctx.anchors(&anchors_u32)?;
                self.gpu = Some(RotAcfGpuState {
                    ctx: ctx.clone(),
                    anchors: anchors_gpu,
                    kind: self.orientation_kind,
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
        let orient_gpu = {
            if let Some(gpu) = &self.gpu {
                let coords = convert_coords(&chunk.coords);
                let orient = match gpu.kind {
                    OrientationKind::Plane => gpu.ctx.orientation_plane(
                        &coords,
                        chunk.coords.len() / chunk.n_frames,
                        n_frames,
                        &gpu.anchors,
                        self.length_scale as f32,
                    )?,
                    OrientationKind::Vector => gpu.ctx.orientation_vector(
                        &coords,
                        chunk.coords.len() / chunk.n_frames,
                        n_frames,
                        &gpu.anchors,
                        self.length_scale as f32,
                    )?,
                };
                used_gpu = true;
                Some(orient)
            } else {
                None
            }
        };
        #[cfg(not(feature = "cuda"))]
        let _orient_gpu = ();

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
                    let orient = orient_gpu.as_ref().unwrap();
                    for g in 0..self.n_groups {
                        let v = orient[frame * self.n_groups + g];
                        let base = g * 3;
                        self.sample_f32[base] = v.x as f32;
                        self.sample_f32[base + 1] = v.y as f32;
                        self.sample_f32[base + 2] = v.z as f32;
                    }
                }
            } else {
                let frame_offset = frame * (chunk.coords.len() / n_frames);
                for g in 0..self.n_groups {
                    let [a, b, c] = self.anchors.as_ref().unwrap()[g];
                    let pa = chunk.coords[frame_offset + a];
                    let pb = chunk.coords[frame_offset + b];
                    let vec = match self.orientation_kind {
                        OrientationKind::Plane => {
                            let pc = chunk.coords[frame_offset + c];
                            let v1 = [
                                (pa[0] - pb[0]) as f64 * self.length_scale,
                                (pa[1] - pb[1]) as f64 * self.length_scale,
                                (pa[2] - pb[2]) as f64 * self.length_scale,
                            ];
                            let v2 = [
                                (pa[0] - pc[0]) as f64 * self.length_scale,
                                (pa[1] - pc[1]) as f64 * self.length_scale,
                                (pa[2] - pc[2]) as f64 * self.length_scale,
                            ];
                            cross_unit(v1, v2)
                        }
                        OrientationKind::Vector => {
                            let v = [
                                (pb[0] - pa[0]) as f64 * self.length_scale,
                                (pb[1] - pa[1]) as f64 * self.length_scale,
                                (pb[2] - pa[2]) as f64 * self.length_scale,
                            ];
                            unit(v)
                        }
                    };
                    let base = g * 3;
                    self.sample_f32[base] = vec[0] as f32;
                    self.sample_f32[base + 1] = vec[1] as f32;
                    self.sample_f32[base + 2] = vec[2] as f32;
                }
            }

            match self.resolved_mode {
                LagMode::MultiTau => {
                    if let Some(buffer) = &mut self.multi_tau {
                        let cols = 2 * (self.type_counts.len() + 1);
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
                            accumulate_rotacf(
                                acc,
                                lag_idx,
                                cols,
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
                        let cols = 2 * (self.type_counts.len() + 1);
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
                            accumulate_rotacf(
                                acc,
                                lag_idx,
                                cols,
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
        let cols = 2 * (n_types + 1);

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
                            let time_binning = (
                                self.time_binning.eps_num as f32,
                                self.time_binning.eps_add as f32,
                            );
                            let (corr_gpu, corr_p2_gpu, n_diff_gpu) = gpu.ctx.rotacf_time_lag(
                                &self.series,
                                &times_f32,
                                &type_ids_u32,
                                &type_counts_u32,
                                self.n_groups,
                                n_types,
                                ndframe,
                                None,
                                self.dt_decimation.map(|d| (d.cut1, d.stride1, d.cut2, d.stride2)),
                                time_binning,
                            )?;
                            if !corr_gpu.is_empty() && !corr_p2_gpu.is_empty() {
                                let mut lags = Vec::new();
                                for lag in 1..=ndframe {
                                    if lag_allowed(lag, self.dt_decimation) {
                                        lags.push(lag);
                                    }
                                }
                                let stride = n_types + 1;
                                let mut acc = vec![0.0f64; lags.len() * cols];
                                let mut counts = vec![0u64; lags.len()];
                                for (idx, &lag) in lags.iter().enumerate() {
                                    counts[idx] = n_diff_gpu[lag] as u64;
                                    let base = lag * stride;
                                    let out_base = idx * cols;
                                    for t in 0..stride {
                                        acc[out_base + t] = corr_gpu[base + t] as f64;
                                        acc[out_base + stride + t] =
                                            corr_p2_gpu[base + t] as f64;
                                    }
                                }
                                let (time, data) = finalize_rotacf(
                                    &lags,
                                    &acc,
                                    &counts,
                                    dt0,
                                    cols,
                                    self.p2_legendre,
                                );
                                return Ok(PlanOutput::TimeSeries {
                                    time,
                                    data,
                                    rows: lags.len() + 1,
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
                            accumulate_rotacf(
                                acc_ref,
                                lag_idx,
                                cols,
                                n_groups,
                                type_ids,
                                type_counts,
                                cur,
                                old,
                            );
                        });
                    }
                    let counts = buffer.n_pairs().to_vec();
                    let (time, data) = finalize_rotacf(
                        &lags,
                        &acc,
                        &counts,
                        dt0,
                        cols,
                        self.p2_legendre,
                    );
                    return Ok(PlanOutput::TimeSeries {
                        time,
                        data,
                        rows: lags.len() + 1,
                        cols,
                    });
                }

                let (lags, acc, counts) = rotacf_fft(
                    &self.series,
                    n_frames,
                    self.n_groups,
                    &self.type_ids,
                    &self.type_counts,
                    self.dt_decimation,
                )?;
                let (time, data) = finalize_rotacf(
                    &lags,
                    &acc,
                    &counts,
                    dt0,
                    cols,
                    self.p2_legendre,
                );
                Ok(PlanOutput::TimeSeries {
                    time,
                    data,
                    rows: lags.len() + 1,
                    cols,
                })
            }
            LagMode::Ring => {
                let counts = self
                    .ring
                    .as_ref()
                    .map(|r| r.n_pairs().to_vec())
                    .unwrap_or_default();
                let (time, data) = finalize_rotacf(
                    &self.lags,
                    &self.acc,
                    &counts,
                    dt0,
                    cols,
                    self.p2_legendre,
                );
                Ok(PlanOutput::TimeSeries {
                    time,
                    data,
                    rows: self.lags.len() + 1,
                    cols,
                })
            }
            LagMode::MultiTau => {
                let counts = self
                    .multi_tau
                    .as_ref()
                    .map(|m| m.n_pairs().to_vec())
                    .unwrap_or_default();
                let (time, data) = finalize_rotacf(
                    &self.lags,
                    &self.acc,
                    &counts,
                    dt0,
                    cols,
                    self.p2_legendre,
                );
                Ok(PlanOutput::TimeSeries {
                    time,
                    data,
                    rows: self.lags.len() + 1,
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

fn accumulate_rotacf(
    acc: &mut [f64],
    lag_idx: usize,
    cols: usize,
    n_groups: usize,
    type_ids: &[usize],
    type_counts: &[usize],
    cur: &[f32],
    old: &[f32],
) {
    let n_types = type_counts.len();
    let n_groups_f = n_groups as f64;
    let base = lag_idx * cols;
    for g in 0..n_groups {
        let idx = g * 3;
        let ux = cur[idx] as f64;
        let uy = cur[idx + 1] as f64;
        let uz = cur[idx + 2] as f64;
        let vx = old[idx] as f64;
        let vy = old[idx + 1] as f64;
        let vz = old[idx + 2] as f64;
        let dot = ux * vx + uy * vy + uz * vz;
        let dot2 = dot * dot;
        let type_id = type_ids[g];
        let type_count = type_counts[type_id] as f64;
        acc[base + type_id] += dot / type_count;
        acc[base + n_types] += dot / n_groups_f;
        acc[base + (n_types + 1) + type_id] += dot2 / type_count;
        acc[base + (n_types + 1) + n_types] += dot2 / n_groups_f;
    }
}

fn finalize_rotacf(
    lags: &[usize],
    acc: &[f64],
    counts: &[u64],
    dt0: f64,
    cols: usize,
    p2_legendre: bool,
) -> (Vec<f32>, Vec<f32>) {
    let n_types = cols / 2 - 1;
    let mut time = Vec::with_capacity(lags.len() + 1);
    let mut data = vec![0.0f32; (lags.len() + 1) * cols];
    time.push(0.0);
    for t in 0..(n_types + 1) {
        data[t] = 1.0;
        data[(n_types + 1) + t] = 1.0;
    }
    for (idx, &lag) in lags.iter().enumerate() {
        time.push((dt0 * lag as f64) as f32);
        let count = counts.get(idx).copied().unwrap_or(0) as f64;
        if count == 0.0 {
            continue;
        }
        let base = idx * cols;
        let out_base = (idx + 1) * cols;
        for t in 0..(n_types + 1) {
            let p1 = acc[base + t] / count;
            let mut p2 = acc[base + (n_types + 1) + t] / count;
            if p2_legendre {
                p2 = 1.5 * p2 - 0.5;
            }
            data[out_base + t] = p1 as f32;
            data[out_base + (n_types + 1) + t] = p2 as f32;
        }
    }
    (time, data)
}

fn rotacf_fft(
    series: &[f32],
    n_frames: usize,
    n_groups: usize,
    type_ids: &[usize],
    type_counts: &[usize],
    dt_decimation: Option<DtDecimation>,
) -> TrajResult<(Vec<usize>, Vec<f64>, Vec<u64>)> {
    let n_types = type_counts.len();
    let cols = 2 * (n_types + 1);
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
        let corr_x = autocorr_real(&x)?;
        let corr_y = autocorr_real(&y)?;
        let corr_z = autocorr_real(&z)?;
        let corr_xx = autocorr_real(&x.iter().map(|v| v * v).collect::<Vec<_>>())?;
        let corr_yy = autocorr_real(&y.iter().map(|v| v * v).collect::<Vec<_>>())?;
        let corr_zz = autocorr_real(&z.iter().map(|v| v * v).collect::<Vec<_>>())?;
        let corr_xy = autocorr_real(&x.iter().zip(y.iter()).map(|(a, b)| a * b).collect::<Vec<_>>())?;
        let corr_xz = autocorr_real(&x.iter().zip(z.iter()).map(|(a, b)| a * b).collect::<Vec<_>>())?;
        let corr_yz = autocorr_real(&y.iter().zip(z.iter()).map(|(a, b)| a * b).collect::<Vec<_>>())?;

        let type_id = type_ids[g];
        let type_count = type_counts[type_id] as f64;
        for (out_idx, &lag) in lags.iter().enumerate() {
            let base = out_idx * cols;
            let dot = (corr_x[lag] + corr_y[lag] + corr_z[lag]) as f64;
            let dot2 = (corr_xx[lag]
                + corr_yy[lag]
                + corr_zz[lag]
                + 2.0 * (corr_xy[lag] + corr_xz[lag] + corr_yz[lag])) as f64;
            acc[base + type_id] += dot / type_count;
            acc[base + n_types] += dot / n_groups_f;
            acc[base + (n_types + 1) + type_id] += dot2 / type_count;
            acc[base + (n_types + 1) + n_types] += dot2 / n_groups_f;
        }
    }

    Ok((lags, acc, counts))
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

fn resolve_orientation(spec: &OrientationSpec, groups: &GroupMap, _system: &System) -> TrajResult<Vec<[usize; 3]>> {
    let mut anchors = Vec::with_capacity(groups.n_groups());
    match spec {
        OrientationSpec::PlaneIndices(idxs) => {
            for atoms in &groups.groups {
                if atoms.len() < idxs[0].max(idxs[1]).max(idxs[2]) {
                    return Err(TrajError::Mismatch("orientation index out of range".into()));
                }
                anchors.push([
                    atoms[idxs[0] - 1],
                    atoms[idxs[1] - 1],
                    atoms[idxs[2] - 1],
                ]);
            }
        }
        OrientationSpec::VectorIndices(idxs) => {
            for atoms in &groups.groups {
                if atoms.len() < idxs[0].max(idxs[1]) {
                    return Err(TrajError::Mismatch("orientation index out of range".into()));
                }
                anchors.push([
                    atoms[idxs[0] - 1],
                    atoms[idxs[1] - 1],
                    atoms[idxs[1] - 1],
                ]);
            }
        }
        OrientationSpec::PlaneSelections(sels) => {
            let sets: Vec<HashSet<u32>> = sels
                .iter()
                .map(|sel| sel.indices.iter().copied().collect())
                .collect();
            for atoms in &groups.groups {
                let a = pick_atom(atoms, &sets[0])?;
                let b = pick_atom(atoms, &sets[1])?;
                let c = pick_atom(atoms, &sets[2])?;
                anchors.push([a, b, c]);
            }
        }
        OrientationSpec::VectorSelections(sels) => {
            let sets: Vec<HashSet<u32>> = sels
                .iter()
                .map(|sel| sel.indices.iter().copied().collect())
                .collect();
            for atoms in &groups.groups {
                let a = pick_atom(atoms, &sets[0])?;
                let b = pick_atom(atoms, &sets[1])?;
                anchors.push([a, b, b]);
            }
        }
    }
    Ok(anchors)
}

fn pick_atom(atoms: &[usize], set: &HashSet<u32>) -> TrajResult<usize> {
    for &atom in atoms {
        if set.contains(&(atom as u32)) {
            return Ok(atom);
        }
    }
    Err(TrajError::Mismatch(
        "orientation selection missing atom in group".into(),
    ))
}

fn cross_unit(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    let x = a[1] * b[2] - a[2] * b[1];
    let y = a[2] * b[0] - a[0] * b[2];
    let z = a[0] * b[1] - a[1] * b[0];
    let norm = (x * x + y * y + z * z).sqrt();
    if norm == 0.0 {
        [0.0, 0.0, 0.0]
    } else {
        [x / norm, y / norm, z / norm]
    }
}

fn unit(v: [f64; 3]) -> [f64; 3] {
    let norm = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt();
    if norm == 0.0 {
        [0.0, 0.0, 0.0]
    } else {
        [v[0] / norm, v[1] / norm, v[2] / norm]
    }
}
