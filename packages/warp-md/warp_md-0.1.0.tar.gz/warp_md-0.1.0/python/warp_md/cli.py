from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import numpy as np

_API_IMPORT_ERROR: Optional[Exception]
try:
    from . import (
        BondAngleDistributionPlan,
        BondLengthDistributionPlan,
        ChainRgPlan,
        ConductivityPlan,
        ContourLengthPlan,
        DielectricPlan,
        DipoleAlignmentPlan,
        EndToEndPlan,
        EquipartitionPlan,
        HbondPlan,
        IonPairCorrelationPlan,
        MsdPlan,
        PersistenceLengthPlan,
        RdfPlan,
        RgPlan,
        RmsdPlan,
        RotAcfPlan,
        StructureFactorPlan,
        System,
        Trajectory,
        WaterCountPlan,
    )
    _API_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - import guard for help/metadata usage
    BondAngleDistributionPlan = None  # type: ignore[assignment]
    BondLengthDistributionPlan = None  # type: ignore[assignment]
    ChainRgPlan = None  # type: ignore[assignment]
    ConductivityPlan = None  # type: ignore[assignment]
    ContourLengthPlan = None  # type: ignore[assignment]
    DielectricPlan = None  # type: ignore[assignment]
    DipoleAlignmentPlan = None  # type: ignore[assignment]
    EndToEndPlan = None  # type: ignore[assignment]
    EquipartitionPlan = None  # type: ignore[assignment]
    HbondPlan = None  # type: ignore[assignment]
    IonPairCorrelationPlan = None  # type: ignore[assignment]
    MsdPlan = None  # type: ignore[assignment]
    PersistenceLengthPlan = None  # type: ignore[assignment]
    RdfPlan = None  # type: ignore[assignment]
    RgPlan = None  # type: ignore[assignment]
    RmsdPlan = None  # type: ignore[assignment]
    RotAcfPlan = None  # type: ignore[assignment]
    StructureFactorPlan = None  # type: ignore[assignment]
    System = None  # type: ignore[assignment]
    Trajectory = None  # type: ignore[assignment]
    WaterCountPlan = None  # type: ignore[assignment]
    _API_IMPORT_ERROR = exc
from .builder import charges_from_selections, charges_from_table, group_types_from_selections


def _require_api() -> None:
    if _API_IMPORT_ERROR is not None:
        raise RuntimeError(
            "warp-md Python bindings are unavailable. Run `maturin develop` or install warp-md."
        ) from _API_IMPORT_ERROR


def _load_config(path: str) -> Dict[str, Any]:
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    if cfg_path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("YAML config requires PyYAML installed") from exc
        return yaml.safe_load(cfg_path.read_text())
    return json.loads(cfg_path.read_text())


def _as_tuple(value: Any, size: int, label: str) -> Optional[tuple[Any, ...]]:
    if value is None:
        return None
    if isinstance(value, tuple):
        if len(value) != size:
            raise ValueError(f"{label} must have length {size}")
        return value
    if isinstance(value, list):
        if len(value) != size:
            raise ValueError(f"{label} must have length {size}")
        return tuple(value)
    raise ValueError(f"{label} must be a list/tuple of length {size}")


def _pick(spec: Dict[str, Any], keys: Iterable[str]) -> Dict[str, Any]:
    return {k: spec[k] for k in keys if k in spec and spec[k] is not None}


def _normalize_system_spec(spec: Any) -> Dict[str, Any]:
    if isinstance(spec, str):
        return {"path": spec}
    if isinstance(spec, dict):
        return spec
    raise ValueError("system spec must be a path or object")


def _normalize_traj_spec(spec: Any) -> Dict[str, Any]:
    if isinstance(spec, str):
        return {"path": spec}
    if isinstance(spec, dict):
        return spec
    raise ValueError("trajectory spec must be a path or object")


def _load_system(spec: Dict[str, Any]) -> System:
    _require_api()
    path = spec.get("path")
    if not path:
        raise ValueError("system.path is required")
    fmt = spec.get("format")
    if fmt is None:
        fmt = Path(path).suffix.lower().lstrip(".")
    if fmt == "pdb":
        return System.from_pdb(path)
    if fmt == "gro":
        return System.from_gro(path)
    raise ValueError("system.format must be pdb or gro")


def _load_trajectory(spec: Dict[str, Any], system: System) -> Trajectory:
    _require_api()
    path = spec.get("path")
    if not path:
        raise ValueError("trajectory.path is required")
    fmt = spec.get("format")
    if fmt is None:
        fmt = Path(path).suffix.lower().lstrip(".")
    if fmt == "dcd":
        return Trajectory.open_dcd(path, system, length_scale=spec.get("length_scale"))
    if fmt == "xtc":
        return Trajectory.open_xtc(path, system)
    raise ValueError("trajectory.format must be dcd or xtc")


def _select(system: System, expr: str, label: str):
    if not expr:
        raise ValueError(f"{label} selection is required")
    return system.select(expr)


def _resolve_charges(system: System, spec: Any) -> list[float]:
    if isinstance(spec, list):
        return [float(x) for x in spec]
    if isinstance(spec, dict):
        mode = spec.get("from")
        default = spec.get("default", 0.0)
        if mode == "table":
            path = spec.get("path")
            if not path:
                raise ValueError("charges.from=table requires path")
            return charges_from_table(system, path, delimiter=spec.get("delimiter"), default=default)
        if mode == "selections":
            entries = spec.get("entries")
            if not entries:
                raise ValueError("charges.from=selections requires entries")
            return charges_from_selections(system, entries, default=default)
    raise ValueError("charges must be a list or {from: table|selections}")


def _resolve_group_types(
    system: System,
    selection,
    group_by: str,
    spec: Any,
) -> Optional[list[int]]:
    if spec is None:
        return None
    if isinstance(spec, list):
        return [int(x) for x in spec]
    if isinstance(spec, dict):
        if spec.get("from") != "selections":
            raise ValueError("group_types.from must be selections")
        type_selections = spec.get("type_selections")
        if not type_selections:
            raise ValueError("group_types.type_selections required")
        sel_expr = spec.get("selection")
        sel = selection if sel_expr is None else system.select(sel_expr)
        group_by = spec.get("group_by", group_by)
        return group_types_from_selections(system, sel, group_by, type_selections)
    raise ValueError("group_types must be a list or {from: selections}")


def _save_output(path: str, output: Any) -> None:
    out_path = Path(path)
    suffix = out_path.suffix.lower()
    if suffix == "":
        out_path = out_path.with_suffix(".npz")
        suffix = ".npz"

    if suffix == ".npy":
        if not isinstance(output, np.ndarray):
            raise ValueError(".npy output requires a single array")
        np.save(out_path, output)
        return

    if suffix == ".csv":
        if not isinstance(output, np.ndarray):
            raise ValueError(".csv output requires a single array")
        np.savetxt(out_path, output, delimiter=",")
        return

    if suffix == ".json":
        out_path.write_text(json.dumps(_to_jsonable(output), indent=2))
        return

    if suffix == ".npz":
        arrays = _to_npz_dict(output)
        np.savez(out_path, **arrays)
        return

    raise ValueError("output extension must be .npz, .npy, .csv, or .json")


def _to_npz_dict(output: Any) -> Dict[str, np.ndarray]:
    if isinstance(output, np.ndarray):
        return {"data": output}
    if isinstance(output, dict):
        return {str(k): np.asarray(v) for k, v in output.items()}
    if isinstance(output, (list, tuple)):
        return {f"arr_{i}": np.asarray(v) for i, v in enumerate(output)}
    return {"data": np.asarray(output)}


def _to_jsonable(output: Any) -> Any:
    if isinstance(output, np.ndarray):
        return output.tolist()
    if isinstance(output, dict):
        return {str(k): _to_jsonable(v) for k, v in output.items()}
    if isinstance(output, (list, tuple)):
        return [_to_jsonable(v) for v in output]
    if isinstance(output, (np.floating, np.integer)):
        return output.item()
    return output


def _build_rg(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "rg.selection")
    kwargs = _pick(spec, ["mass_weighted"])
    return RgPlan(sel, **kwargs)


def _build_rmsd(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "rmsd.selection")
    kwargs = _pick(spec, ["reference", "align"])
    return RmsdPlan(sel, **kwargs)


def _build_msd(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "msd.selection")
    group_by = spec.get("group_by", "resid")
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(
        spec,
        [
            "axis",
            "length_scale",
            "frame_decimation",
            "dt_decimation",
            "time_binning",
            "lag_mode",
            "max_lag",
            "memory_budget_bytes",
            "multi_tau_m",
            "multi_tau_levels",
        ],
    )
    if "axis" in kwargs:
        kwargs["axis"] = _as_tuple(kwargs["axis"], 3, "axis")
    if "frame_decimation" in kwargs:
        kwargs["frame_decimation"] = _as_tuple(kwargs["frame_decimation"], 2, "frame_decimation")
    if "dt_decimation" in kwargs:
        kwargs["dt_decimation"] = _as_tuple(kwargs["dt_decimation"], 4, "dt_decimation")
    if "time_binning" in kwargs:
        kwargs["time_binning"] = _as_tuple(kwargs["time_binning"], 2, "time_binning")
    if group_types is not None:
        kwargs["group_types"] = group_types
    return MsdPlan(sel, group_by=group_by, **kwargs)


def _build_rotacf(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "rotacf.selection")
    group_by = spec.get("group_by", "resid")
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(
        spec,
        [
            "orientation",
            "p2_legendre",
            "length_scale",
            "frame_decimation",
            "dt_decimation",
            "time_binning",
            "lag_mode",
            "max_lag",
            "memory_budget_bytes",
            "multi_tau_m",
            "multi_tau_levels",
        ],
    )
    if "orientation" in kwargs:
        orient = kwargs["orientation"]
        if not isinstance(orient, (list, tuple)) or len(orient) not in (2, 3):
            raise ValueError("rotacf.orientation must be length 2 or 3")
    if "frame_decimation" in kwargs:
        kwargs["frame_decimation"] = _as_tuple(kwargs["frame_decimation"], 2, "frame_decimation")
    if "dt_decimation" in kwargs:
        kwargs["dt_decimation"] = _as_tuple(kwargs["dt_decimation"], 4, "dt_decimation")
    if "time_binning" in kwargs:
        kwargs["time_binning"] = _as_tuple(kwargs["time_binning"], 2, "time_binning")
    if group_types is not None:
        kwargs["group_types"] = group_types
    return RotAcfPlan(sel, group_by=group_by, **kwargs)


def _build_conductivity(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "conductivity.selection")
    group_by = spec.get("group_by", "resid")
    charges_spec = spec.get("charges")
    if charges_spec is None:
        raise ValueError("conductivity.charges is required")
    charges = _resolve_charges(system, charges_spec)
    temperature = spec.get("temperature")
    if temperature is None:
        raise ValueError("conductivity.temperature is required")
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(
        spec,
        [
            "transference",
            "length_scale",
            "frame_decimation",
            "dt_decimation",
            "time_binning",
            "lag_mode",
            "max_lag",
            "memory_budget_bytes",
            "multi_tau_m",
            "multi_tau_levels",
        ],
    )
    if "frame_decimation" in kwargs:
        kwargs["frame_decimation"] = _as_tuple(kwargs["frame_decimation"], 2, "frame_decimation")
    if "dt_decimation" in kwargs:
        kwargs["dt_decimation"] = _as_tuple(kwargs["dt_decimation"], 4, "dt_decimation")
    if "time_binning" in kwargs:
        kwargs["time_binning"] = _as_tuple(kwargs["time_binning"], 2, "time_binning")
    if group_types is not None:
        kwargs["group_types"] = group_types
    return ConductivityPlan(sel, charges, temperature, group_by=group_by, **kwargs)


def _build_dielectric(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "dielectric.selection")
    group_by = spec.get("group_by", "resid")
    charges_spec = spec.get("charges")
    if charges_spec is None:
        raise ValueError("dielectric.charges is required")
    charges = _resolve_charges(system, charges_spec)
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(spec, ["length_scale"])
    if group_types is not None:
        kwargs["group_types"] = group_types
    return DielectricPlan(sel, charges, group_by=group_by, **kwargs)


def _build_dipole_alignment(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "dipole_alignment.selection")
    group_by = spec.get("group_by", "resid")
    charges_spec = spec.get("charges")
    if charges_spec is None:
        raise ValueError("dipole_alignment.charges is required")
    charges = _resolve_charges(system, charges_spec)
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(spec, ["length_scale"])
    if group_types is not None:
        kwargs["group_types"] = group_types
    return DipoleAlignmentPlan(sel, charges, group_by=group_by, **kwargs)


def _build_ion_pair(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "ion_pair_correlation.selection")
    group_by = spec.get("group_by", "resid")
    rclust_cat = spec.get("rclust_cat")
    rclust_ani = spec.get("rclust_ani")
    if rclust_cat is None or rclust_ani is None:
        raise ValueError("ion_pair_correlation.rclust_cat and rclust_ani are required")
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(
        spec,
        [
            "cation_type",
            "anion_type",
            "max_cluster",
            "length_scale",
            "lag_mode",
            "max_lag",
            "memory_budget_bytes",
            "multi_tau_m",
            "multi_tau_levels",
        ],
    )
    if group_types is not None:
        kwargs["group_types"] = group_types
    return IonPairCorrelationPlan(sel, rclust_cat, rclust_ani, group_by=group_by, **kwargs)


def _build_structure_factor(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "structure_factor.selection")
    bins = spec.get("bins")
    r_max = spec.get("r_max")
    q_bins = spec.get("q_bins")
    q_max = spec.get("q_max")
    if None in (bins, r_max, q_bins, q_max):
        raise ValueError("structure_factor requires bins, r_max, q_bins, q_max")
    kwargs = _pick(spec, ["pbc", "length_scale"])
    return StructureFactorPlan(sel, bins, r_max, q_bins, q_max, **kwargs)


def _build_water_count(system: System, spec: Dict[str, Any]):
    water_sel = _select(system, spec.get("water_selection"), "water_count.water_selection")
    center_sel = _select(system, spec.get("center_selection"), "water_count.center_selection")
    box_unit = spec.get("box_unit")
    region_size = spec.get("region_size")
    if box_unit is None or region_size is None:
        raise ValueError("water_count requires box_unit and region_size")
    kwargs = _pick(spec, ["shift", "length_scale"])
    kwargs["box_unit"] = _as_tuple(box_unit, 3, "box_unit")
    kwargs["region_size"] = _as_tuple(region_size, 3, "region_size")
    if "shift" in kwargs:
        kwargs["shift"] = _as_tuple(kwargs["shift"], 3, "shift")
    return WaterCountPlan(water_sel, center_sel, **kwargs)


def _build_equipartition(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "equipartition.selection")
    group_by = spec.get("group_by", "resid")
    group_types = _resolve_group_types(system, sel, group_by, spec.get("group_types"))
    kwargs = _pick(spec, ["velocity_scale", "length_scale"])
    if group_types is not None:
        kwargs["group_types"] = group_types
    return EquipartitionPlan(sel, group_by=group_by, **kwargs)


def _build_hbond(system: System, spec: Dict[str, Any]):
    donors = _select(system, spec.get("donors"), "hbond.donors")
    acceptors = _select(system, spec.get("acceptors"), "hbond.acceptors")
    dist_cutoff = spec.get("dist_cutoff")
    if dist_cutoff is None:
        raise ValueError("hbond.dist_cutoff is required")
    hydrogens_expr = spec.get("hydrogens")
    angle_cutoff = spec.get("angle_cutoff")
    if hydrogens_expr:
        hydrogens = _select(system, hydrogens_expr, "hbond.hydrogens")
        return HbondPlan(donors, acceptors, dist_cutoff, hydrogens=hydrogens, angle_cutoff=angle_cutoff)
    return HbondPlan(donors, acceptors, dist_cutoff)


def _build_rdf(system: System, spec: Dict[str, Any]):
    sel_a = _select(system, spec.get("sel_a"), "rdf.sel_a")
    sel_b = _select(system, spec.get("sel_b"), "rdf.sel_b")
    bins = spec.get("bins")
    r_max = spec.get("r_max")
    if bins is None or r_max is None:
        raise ValueError("rdf requires bins and r_max")
    kwargs = _pick(spec, ["pbc"])
    return RdfPlan(sel_a, sel_b, bins, r_max, **kwargs)


def _build_end_to_end(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "end_to_end.selection")
    return EndToEndPlan(sel)


def _build_contour_length(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "contour_length.selection")
    return ContourLengthPlan(sel)


def _build_chain_rg(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "chain_rg.selection")
    return ChainRgPlan(sel)


def _build_bond_length(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "bond_length_distribution.selection")
    bins = spec.get("bins")
    r_max = spec.get("r_max")
    if bins is None or r_max is None:
        raise ValueError("bond_length_distribution requires bins and r_max")
    return BondLengthDistributionPlan(sel, bins, r_max)


def _build_bond_angle(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "bond_angle_distribution.selection")
    bins = spec.get("bins")
    if bins is None:
        raise ValueError("bond_angle_distribution requires bins")
    kwargs = _pick(spec, ["degrees"])
    return BondAngleDistributionPlan(sel, bins, **kwargs)


def _build_persistence(system: System, spec: Dict[str, Any]):
    sel = _select(system, spec.get("selection"), "persistence_length.selection")
    return PersistenceLengthPlan(sel)


PLAN_BUILDERS = {
    "rg": _build_rg,
    "rmsd": _build_rmsd,
    "msd": _build_msd,
    "rotacf": _build_rotacf,
    "conductivity": _build_conductivity,
    "dielectric": _build_dielectric,
    "dipole_alignment": _build_dipole_alignment,
    "ion_pair_correlation": _build_ion_pair,
    "structure_factor": _build_structure_factor,
    "water_count": _build_water_count,
    "equipartition": _build_equipartition,
    "hbond": _build_hbond,
    "rdf": _build_rdf,
    "end_to_end": _build_end_to_end,
    "contour_length": _build_contour_length,
    "chain_rg": _build_chain_rg,
    "bond_length_distribution": _build_bond_length,
    "bond_angle_distribution": _build_bond_angle,
    "persistence_length": _build_persistence,
}


CLI_TO_PLAN = {
    "rg": "rg",
    "rmsd": "rmsd",
    "msd": "msd",
    "rotacf": "rotacf",
    "conductivity": "conductivity",
    "dielectric": "dielectric",
    "dipole-alignment": "dipole_alignment",
    "ion-pair-correlation": "ion_pair_correlation",
    "structure-factor": "structure_factor",
    "water-count": "water_count",
    "equipartition": "equipartition",
    "hbond": "hbond",
    "rdf": "rdf",
    "end-to-end": "end_to_end",
    "contour-length": "contour_length",
    "chain-rg": "chain_rg",
    "bond-length-distribution": "bond_length_distribution",
    "bond-angle-distribution": "bond_angle_distribution",
    "persistence-length": "persistence_length",
}


def _default_out(name: str, output_dir: str, used: Dict[str, int]) -> str:
    count = used.get(name, 0)
    used[name] = count + 1
    suffix = "" if count == 0 else f"_{count}"
    return str(Path(output_dir) / f"{name}{suffix}.npz")


def run_config(config_path: str, dry_run: bool = False) -> None:
    cfg = _load_config(config_path)
    system_spec = _normalize_system_spec(cfg.get("system") or cfg.get("topology"))
    traj_spec = _normalize_traj_spec(cfg.get("trajectory") or cfg.get("traj"))
    system = _load_system(system_spec)
    default_device = cfg.get("device", "auto")
    default_chunk = cfg.get("chunk_frames")
    output_dir = cfg.get("output_dir", ".")
    if not dry_run:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    analyses = cfg.get("analyses")
    if not analyses:
        raise ValueError("config.analyses is required")

    used_names: Dict[str, int] = {}
    for item in analyses:
        name = item.get("name")
        if name not in PLAN_BUILDERS:
            alt_name = name.replace("-", "_") if isinstance(name, str) else name
            if alt_name not in PLAN_BUILDERS:
                raise ValueError(f"unknown analysis name: {name}")
            name = alt_name
        out_path = item.get("out") or _default_out(name, output_dir, used_names)
        if dry_run:
            print(f"{name} -> {out_path}")
            continue
        plan = PLAN_BUILDERS[name](system, item)
        traj = _load_trajectory(traj_spec, system)
        device = item.get("device", default_device)
        chunk = item.get("chunk_frames", default_chunk)
        output = plan.run(traj, system, chunk_frames=chunk, device=device)
        _save_output(out_path, output)
        print(f"{name}: wrote {out_path}")


def list_plans() -> None:
    for name in sorted(CLI_TO_PLAN.keys()):
        print(name)


def example_config() -> None:
    example = {
        "system": {"path": "topology.pdb"},
        "trajectory": {"path": "traj.xtc"},
        "device": "auto",
        "chunk_frames": 500,
        "output_dir": "outputs",
        "analyses": [
            {
                "name": "rg",
                "selection": "protein",
                "mass_weighted": False,
            },
            {
                "name": "rdf",
                "sel_a": "resname SOL and name OW",
                "sel_b": "resname SOL and name OW",
                "bins": 200,
                "r_max": 10.0,
            },
        ],
    }
    print(json.dumps(example, indent=2))


def _split_values(raw: str) -> list[str]:
    if "," in raw:
        parts = [part.strip() for part in raw.split(",")]
    else:
        parts = raw.split()
    return [part for part in parts if part]


def _parse_float_tuple(raw: str, size: int, label: str) -> tuple[float, ...]:
    values = _split_values(raw)
    if len(values) != size:
        raise ValueError(f"{label} must have {size} values")
    return tuple(float(v) for v in values)


def _parse_int_tuple(raw: str, size: int, label: str) -> tuple[int, ...]:
    values = _split_values(raw)
    if len(values) != size:
        raise ValueError(f"{label} must have {size} values")
    return tuple(int(v) for v in values)


def _parse_int_list(raw: str, label: str) -> list[int]:
    values = _split_values(raw)
    if not values:
        raise ValueError(f"{label} must have at least one value")
    return [int(v) for v in values]


def _parse_json_list(raw: str, label: str) -> list[Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if not isinstance(data, list):
        raise ValueError(f"{label} must be a JSON list")
    return data


def _parse_charges_arg(raw: str, system: System) -> list[float]:
    if raw.startswith("table:"):
        path = raw[len("table:") :].strip()
        if not path:
            raise ValueError("charges table path is required")
        return charges_from_table(system, path)
    if raw.startswith("selections:"):
        payload = raw[len("selections:") :].strip()
        entries = _parse_json_list(payload, "charges selections")
        return charges_from_selections(system, entries)
    data = _parse_json_list(raw, "charges")
    return [float(x) for x in data]


def _parse_group_types_arg(
    raw: Optional[str],
    system: System,
    selection,
    group_by: str,
) -> Optional[list[int]]:
    if raw is None:
        return None
    if raw.startswith("selections:"):
        payload = raw[len("selections:") :].strip()
        if payload.startswith("["):
            selections = _parse_json_list(payload, "group_types selections")
        else:
            selections = [s.strip() for s in payload.split(",") if s.strip()]
        if not selections:
            raise ValueError("group_types selections cannot be empty")
        return group_types_from_selections(system, selection, group_by, selections)
    data = _parse_json_list(raw, "group_types")
    return [int(x) for x in data]


def _summary_from_output(output: Any, analysis: str, out_path: Path) -> Dict[str, Any]:
    if isinstance(output, np.generic):
        output = output.item()
    summary: Dict[str, Any] = {
        "analysis": analysis,
        "out": str(out_path),
    }
    if isinstance(output, np.ndarray):
        summary.update(
            {
                "kind": "array",
                "shape": list(output.shape),
                "dtype": str(output.dtype),
                "keys": ["data"],
            }
        )
        return summary
    if isinstance(output, dict):
        summary["kind"] = "dict"
        summary["keys"] = [str(k) for k in output.keys()]
        summary["shapes"] = {str(k): list(np.asarray(v).shape) for k, v in output.items()}
        return summary
    if isinstance(output, (list, tuple)):
        summary["kind"] = "tuple"
        summary["keys"] = [f"arr_{i}" for i in range(len(output))]
        summary["shapes"] = {
            f"arr_{i}": list(np.asarray(v).shape) for i, v in enumerate(output)
        }
        return summary
    summary["kind"] = "scalar"
    summary["value"] = output
    return summary


def _print_summary(summary: Dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(summary, indent=2))
        return
    print(f"analysis: {summary.get('analysis')}")
    print(f"out: {summary.get('out')}")
    print(f"kind: {summary.get('kind')}")
    if "keys" in summary:
        print("keys: " + ", ".join(summary["keys"]))
    if "shape" in summary:
        print(f"shape: {summary['shape']}")
    if "dtype" in summary:
        print(f"dtype: {summary['dtype']}")
    if "value" in summary:
        print(f"value: {summary['value']}")


def _infer_format(path: str) -> str:
    return Path(path).suffix.lower().lstrip(".")


def _load_system_from_args(args: argparse.Namespace) -> System:
    fmt = args.topology_format or _infer_format(args.topology)
    spec = {"path": args.topology, "format": fmt}
    return _load_system(spec)


def _load_traj_from_args(args: argparse.Namespace, system: System) -> Trajectory:
    fmt = args.traj_format or _infer_format(args.traj)
    spec = {
        "path": args.traj,
        "format": fmt,
        "length_scale": args.traj_length_scale,
    }
    return _load_trajectory(spec, system)


def add_shared_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--topology", required=True, help="Topology file (.pdb or .gro)")
    parser.add_argument("--traj", required=True, help="Trajectory file (.dcd or .xtc)")
    parser.add_argument(
        "--topology-format",
        choices=["pdb", "gro"],
        help="Override topology format",
    )
    parser.add_argument(
        "--traj-format",
        choices=["dcd", "xtc"],
        help="Override trajectory format",
    )
    parser.add_argument(
        "--traj-length-scale",
        type=float,
        help="DCD length scale (e.g., 10.0 for nm->A)",
    )
    parser.add_argument("--device", default="auto", help="auto|cpu|cuda|cuda:0")
    parser.add_argument("--chunk-frames", type=int, help="Frames per chunk")
    parser.add_argument("--out", help="Output path (.npz/.npy/.csv/.json)")
    summary_group = parser.add_mutually_exclusive_group()
    summary_group.add_argument(
        "--print-summary",
        dest="print_summary",
        action="store_true",
        help="Print a JSON/text summary to stdout",
    )
    summary_group.add_argument(
        "--no-summary",
        dest="print_summary",
        action="store_false",
        help="Disable summary output",
    )
    parser.set_defaults(print_summary=True)
    parser.add_argument(
        "--summary-format",
        choices=["json", "text"],
        default="json",
        help="Summary format",
    )


def add_dynamics_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--frame-decimation",
        help="start,stride (e.g., 0,10)",
    )
    parser.add_argument(
        "--dt-decimation",
        help="cut1,stride1,cut2,stride2",
    )
    parser.add_argument(
        "--time-binning",
        help="eps_num,eps_add",
    )
    parser.add_argument(
        "--lag-mode",
        choices=["auto", "multi_tau", "ring", "fft"],
        help="Lag mode (auto/multi_tau/ring/fft)",
    )
    parser.add_argument("--max-lag", type=int, help="Max lag (ring mode)")
    parser.add_argument("--memory-budget-bytes", type=int, help="Memory budget")
    parser.add_argument("--multi-tau-m", type=int, help="Multi-tau m")
    parser.add_argument("--multi-tau-levels", type=int, help="Multi-tau levels")


def add_group_types_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--group-types",
        help=(
            "JSON list or selections:<sel1,sel2>. "
            "Example: --group-types '[0,1,1]' or --group-types 'selections:resname NA,resname CL'"
        ),
    )


def setup_rg_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument("--mass-weighted", action="store_true", help="Mass-weighted Rg")


def setup_rmsd_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--reference",
        choices=["topology", "frame0"],
        default="topology",
        help="Reference frame",
    )
    parser.add_argument(
        "--align",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Align before RMSD",
    )


def setup_msd_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument("--axis", help="x,y,z axis components")
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)
    add_dynamics_args(parser)


def setup_rotacf_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument("--orientation", required=True, help="Indices (2 or 3) within group")
    parser.add_argument(
        "--p2-legendre",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use P2 Legendre",
    )
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)
    add_dynamics_args(parser)


def setup_conductivity_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--charges",
        required=True,
        help=(
            "Charges: JSON list, table:path, or selections:[{selection,charge},...]"
        ),
    )
    parser.add_argument("--temperature", type=float, required=True, help="Temperature (K)")
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument(
        "--transference",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Compute transference matrix",
    )
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)
    add_dynamics_args(parser)


def setup_dielectric_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--charges",
        required=True,
        help="Charges: JSON list, table:path, or selections:[{selection,charge},...]",
    )
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)


def setup_dipole_alignment_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--charges",
        required=True,
        help="Charges: JSON list, table:path, or selections:[{selection,charge},...]",
    )
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)


def setup_ion_pair_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument("--rclust-cat", type=float, required=True, help="Cation cutoff")
    parser.add_argument("--rclust-ani", type=float, required=True, help="Anion cutoff")
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument("--cation-type", type=int, default=0, help="Cation type index")
    parser.add_argument("--anion-type", type=int, default=1, help="Anion type index")
    parser.add_argument("--max-cluster", type=int, default=10, help="Max cluster size")
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)
    add_dynamics_args(parser)


def setup_structure_factor_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument("--bins", type=int, required=True, help="r-space bins")
    parser.add_argument("--r-max", type=float, required=True, help="r-space max (A)")
    parser.add_argument("--q-bins", type=int, required=True, help="q-space bins")
    parser.add_argument("--q-max", type=float, required=True, help="q-space max (1/A)")
    parser.add_argument(
        "--pbc",
        choices=["orthorhombic", "none"],
        default="orthorhombic",
        help="PBC mode",
    )
    parser.add_argument("--length-scale", type=float, help="Length scale")


def setup_water_count_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--water-selection", required=True, help="Water selection")
    parser.add_argument("--center-selection", required=True, help="Center selection")
    parser.add_argument("--box-unit", required=True, help="Box unit (x,y,z)")
    parser.add_argument("--region-size", required=True, help="Region size (x,y,z)")
    parser.add_argument("--shift", help="Shift (x,y,z)")
    parser.add_argument("--length-scale", type=float, help="Length scale")


def setup_equipartition_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument(
        "--group-by",
        choices=["resid", "chain", "resid_chain"],
        default="resid",
        help="Group-by mode",
    )
    parser.add_argument("--velocity-scale", type=float, help="Velocity scale")
    parser.add_argument("--length-scale", type=float, help="Length scale")
    add_group_types_args(parser)


def setup_hbond_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--donors", required=True, help="Donor selection")
    parser.add_argument("--acceptors", required=True, help="Acceptor selection")
    parser.add_argument("--dist-cutoff", type=float, required=True, help="Distance cutoff (A)")
    parser.add_argument("--hydrogens", help="Hydrogen selection")
    parser.add_argument("--angle-cutoff", type=float, help="Angle cutoff (deg)")


def setup_rdf_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--sel-a", required=True, help="Selection A")
    parser.add_argument("--sel-b", required=True, help="Selection B")
    parser.add_argument("--bins", type=int, required=True, help="Number of bins")
    parser.add_argument("--r-max", type=float, required=True, help="Max distance (A)")
    parser.add_argument(
        "--pbc",
        choices=["orthorhombic", "none"],
        default="orthorhombic",
        help="PBC mode",
    )


def setup_end_to_end_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")


def setup_contour_length_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")


def setup_chain_rg_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")


def setup_bond_length_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument("--bins", type=int, required=True, help="Number of bins")
    parser.add_argument("--r-max", type=float, required=True, help="Max distance (A)")


def setup_bond_angle_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")
    parser.add_argument("--bins", type=int, required=True, help="Number of bins")
    parser.add_argument(
        "--degrees",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Return degrees (default true)",
    )


def setup_persistence_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selection", required=True, help="Selection string")


REGISTRY = {
    "rg": setup_rg_args,
    "rmsd": setup_rmsd_args,
    "msd": setup_msd_args,
    "rotacf": setup_rotacf_args,
    "conductivity": setup_conductivity_args,
    "dielectric": setup_dielectric_args,
    "dipole-alignment": setup_dipole_alignment_args,
    "ion-pair-correlation": setup_ion_pair_args,
    "structure-factor": setup_structure_factor_args,
    "water-count": setup_water_count_args,
    "equipartition": setup_equipartition_args,
    "hbond": setup_hbond_args,
    "rdf": setup_rdf_args,
    "end-to-end": setup_end_to_end_args,
    "contour-length": setup_contour_length_args,
    "chain-rg": setup_chain_rg_args,
    "bond-length-distribution": setup_bond_length_args,
    "bond-angle-distribution": setup_bond_angle_args,
    "persistence-length": setup_persistence_args,
}


def _spec_rg(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {
        "selection": args.selection,
        "mass_weighted": args.mass_weighted,
    }


def _spec_rmsd(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {
        "selection": args.selection,
        "reference": args.reference,
        "align": args.align,
    }


def _spec_msd(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
    }
    if args.axis:
        spec["axis"] = _parse_float_tuple(args.axis, 3, "axis")
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    if args.frame_decimation:
        spec["frame_decimation"] = _parse_int_tuple(args.frame_decimation, 2, "frame_decimation")
    if args.dt_decimation:
        spec["dt_decimation"] = _parse_int_tuple(args.dt_decimation, 4, "dt_decimation")
    if args.time_binning:
        spec["time_binning"] = _parse_float_tuple(args.time_binning, 2, "time_binning")
    if args.lag_mode:
        spec["lag_mode"] = args.lag_mode
    if args.max_lag is not None:
        spec["max_lag"] = args.max_lag
    if args.memory_budget_bytes is not None:
        spec["memory_budget_bytes"] = args.memory_budget_bytes
    if args.multi_tau_m is not None:
        spec["multi_tau_m"] = args.multi_tau_m
    if args.multi_tau_levels is not None:
        spec["multi_tau_levels"] = args.multi_tau_levels
    selection = _select(system, args.selection, "msd.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_rotacf(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
        "p2_legendre": args.p2_legendre,
    }
    orient = _parse_int_list(args.orientation, "orientation")
    if len(orient) not in (2, 3):
        raise ValueError("orientation must have 2 or 3 indices")
    spec["orientation"] = orient
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    if args.frame_decimation:
        spec["frame_decimation"] = _parse_int_tuple(args.frame_decimation, 2, "frame_decimation")
    if args.dt_decimation:
        spec["dt_decimation"] = _parse_int_tuple(args.dt_decimation, 4, "dt_decimation")
    if args.time_binning:
        spec["time_binning"] = _parse_float_tuple(args.time_binning, 2, "time_binning")
    if args.lag_mode:
        spec["lag_mode"] = args.lag_mode
    if args.max_lag is not None:
        spec["max_lag"] = args.max_lag
    if args.memory_budget_bytes is not None:
        spec["memory_budget_bytes"] = args.memory_budget_bytes
    if args.multi_tau_m is not None:
        spec["multi_tau_m"] = args.multi_tau_m
    if args.multi_tau_levels is not None:
        spec["multi_tau_levels"] = args.multi_tau_levels
    selection = _select(system, args.selection, "rotacf.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_conductivity(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
        "temperature": args.temperature,
        "transference": args.transference,
        "charges": _parse_charges_arg(args.charges, system),
    }
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    if args.frame_decimation:
        spec["frame_decimation"] = _parse_int_tuple(args.frame_decimation, 2, "frame_decimation")
    if args.dt_decimation:
        spec["dt_decimation"] = _parse_int_tuple(args.dt_decimation, 4, "dt_decimation")
    if args.time_binning:
        spec["time_binning"] = _parse_float_tuple(args.time_binning, 2, "time_binning")
    if args.lag_mode:
        spec["lag_mode"] = args.lag_mode
    if args.max_lag is not None:
        spec["max_lag"] = args.max_lag
    if args.memory_budget_bytes is not None:
        spec["memory_budget_bytes"] = args.memory_budget_bytes
    if args.multi_tau_m is not None:
        spec["multi_tau_m"] = args.multi_tau_m
    if args.multi_tau_levels is not None:
        spec["multi_tau_levels"] = args.multi_tau_levels
    selection = _select(system, args.selection, "conductivity.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_dielectric(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
        "charges": _parse_charges_arg(args.charges, system),
    }
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    selection = _select(system, args.selection, "dielectric.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_dipole_alignment(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
        "charges": _parse_charges_arg(args.charges, system),
    }
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    selection = _select(system, args.selection, "dipole_alignment.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_ion_pair(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
        "rclust_cat": args.rclust_cat,
        "rclust_ani": args.rclust_ani,
        "cation_type": args.cation_type,
        "anion_type": args.anion_type,
        "max_cluster": args.max_cluster,
    }
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    if args.lag_mode:
        spec["lag_mode"] = args.lag_mode
    if args.max_lag is not None:
        spec["max_lag"] = args.max_lag
    if args.memory_budget_bytes is not None:
        spec["memory_budget_bytes"] = args.memory_budget_bytes
    if args.multi_tau_m is not None:
        spec["multi_tau_m"] = args.multi_tau_m
    if args.multi_tau_levels is not None:
        spec["multi_tau_levels"] = args.multi_tau_levels
    selection = _select(system, args.selection, "ion_pair_correlation.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_structure_factor(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "bins": args.bins,
        "r_max": args.r_max,
        "q_bins": args.q_bins,
        "q_max": args.q_max,
        "pbc": args.pbc,
    }
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    return spec


def _spec_water_count(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "water_selection": args.water_selection,
        "center_selection": args.center_selection,
        "box_unit": _parse_float_tuple(args.box_unit, 3, "box_unit"),
        "region_size": _parse_float_tuple(args.region_size, 3, "region_size"),
    }
    if args.shift:
        spec["shift"] = _parse_float_tuple(args.shift, 3, "shift")
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    return spec


def _spec_equipartition(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "selection": args.selection,
        "group_by": args.group_by,
    }
    if args.velocity_scale is not None:
        spec["velocity_scale"] = args.velocity_scale
    if args.length_scale is not None:
        spec["length_scale"] = args.length_scale
    selection = _select(system, args.selection, "equipartition.selection")
    group_types = _parse_group_types_arg(args.group_types, system, selection, args.group_by)
    if group_types is not None:
        spec["group_types"] = group_types
    return spec


def _spec_hbond(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "donors": args.donors,
        "acceptors": args.acceptors,
        "dist_cutoff": args.dist_cutoff,
    }
    if args.hydrogens:
        if args.angle_cutoff is None:
            raise ValueError("angle_cutoff is required when hydrogens are provided")
        spec["hydrogens"] = args.hydrogens
        spec["angle_cutoff"] = args.angle_cutoff
    return spec


def _spec_rdf(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {
        "sel_a": args.sel_a,
        "sel_b": args.sel_b,
        "bins": args.bins,
        "r_max": args.r_max,
        "pbc": args.pbc,
    }


def _spec_end_to_end(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {"selection": args.selection}


def _spec_contour_length(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {"selection": args.selection}


def _spec_chain_rg(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {"selection": args.selection}


def _spec_bond_length(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {
        "selection": args.selection,
        "bins": args.bins,
        "r_max": args.r_max,
    }


def _spec_bond_angle(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {
        "selection": args.selection,
        "bins": args.bins,
        "degrees": args.degrees,
    }


def _spec_persistence(args: argparse.Namespace, system: System) -> Dict[str, Any]:
    return {"selection": args.selection}


SPEC_BUILDERS = {
    "rg": _spec_rg,
    "rmsd": _spec_rmsd,
    "msd": _spec_msd,
    "rotacf": _spec_rotacf,
    "conductivity": _spec_conductivity,
    "dielectric": _spec_dielectric,
    "dipole-alignment": _spec_dipole_alignment,
    "ion-pair-correlation": _spec_ion_pair,
    "structure-factor": _spec_structure_factor,
    "water-count": _spec_water_count,
    "equipartition": _spec_equipartition,
    "hbond": _spec_hbond,
    "rdf": _spec_rdf,
    "end-to-end": _spec_end_to_end,
    "contour-length": _spec_contour_length,
    "chain-rg": _spec_chain_rg,
    "bond-length-distribution": _spec_bond_length,
    "bond-angle-distribution": _spec_bond_angle,
    "persistence-length": _spec_persistence,
}


def build_plan_from_args(args: argparse.Namespace, system: System):
    plan_name = CLI_TO_PLAN[args.analysis]
    spec = SPEC_BUILDERS[args.analysis](args, system)
    return PLAN_BUILDERS[plan_name](system, spec)


def run_single_analysis(args: argparse.Namespace) -> None:
    system = _load_system_from_args(args)
    traj = _load_traj_from_args(args, system)
    plan = build_plan_from_args(args, system)
    output = plan.run(traj, system, chunk_frames=args.chunk_frames, device=args.device)
    out_path = Path(args.out or f"{args.analysis}.npz")
    _save_output(str(out_path), output)
    if args.print_summary:
        summary = _summary_from_output(output, args.analysis, out_path)
        _print_summary(summary, args.summary_format)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="warp-md")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run analyses from a JSON/YAML config")
    run.add_argument("config", help="path to config.json|yaml")
    run.add_argument("--dry-run", action="store_true", help="validate and show outputs")

    sub.add_parser("list-plans", help="list available analysis names")
    sub.add_parser("example", help="print example config")

    for name, setup in REGISTRY.items():
        help_text = f"Run {name} analysis"
        analysis = sub.add_parser(name, help=help_text, description=help_text)
        add_shared_args(analysis)
        setup(analysis)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "run":
        run_config(args.config, dry_run=args.dry_run)
        return 0
    if args.cmd == "list-plans":
        list_plans()
        return 0
    if args.cmd == "example":
        example_config()
        return 0
    if args.cmd in REGISTRY:
        args.analysis = args.cmd
        run_single_analysis(args)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
