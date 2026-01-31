try:
    from .traj_py import (
        PySystem as System,
        PySelection as Selection,
        PyTrajectory as Trajectory,
        PyRgPlan as RgPlan,
        PyRmsdPlan as RmsdPlan,
        PyMsdPlan as MsdPlan,
        PyRotAcfPlan as RotAcfPlan,
        PyConductivityPlan as ConductivityPlan,
        PyDielectricPlan as DielectricPlan,
        PyDipoleAlignmentPlan as DipoleAlignmentPlan,
        PyIonPairCorrelationPlan as IonPairCorrelationPlan,
        PyStructureFactorPlan as StructureFactorPlan,
        PyWaterCountPlan as WaterCountPlan,
        PyEquipartitionPlan as EquipartitionPlan,
        PyHbondPlan as HbondPlan,
        PyRdfPlan as RdfPlan,
        PyEndToEndPlan as EndToEndPlan,
        PyContourLengthPlan as ContourLengthPlan,
        PyChainRgPlan as ChainRgPlan,
        PyBondLengthDistributionPlan as BondLengthDistributionPlan,
        PyBondAngleDistributionPlan as BondAngleDistributionPlan,
        PyPersistenceLengthPlan as PersistenceLengthPlan,
    )
    _IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - allow CLI help without bindings
    _IMPORT_ERROR = exc

    def _missing(*_args, **_kwargs):
        raise RuntimeError(
            "warp-md Python bindings are unavailable. Run `maturin develop` or install warp-md."
        ) from _IMPORT_ERROR

    class _Missing:
        def __init__(self, *args, **kwargs):
            _missing(*args, **kwargs)

    System = _Missing
    Selection = _Missing
    Trajectory = _Missing
    RgPlan = _Missing
    RmsdPlan = _Missing
    MsdPlan = _Missing
    RotAcfPlan = _Missing
    ConductivityPlan = _Missing
    DielectricPlan = _Missing
    DipoleAlignmentPlan = _Missing
    IonPairCorrelationPlan = _Missing
    StructureFactorPlan = _Missing
    WaterCountPlan = _Missing
    EquipartitionPlan = _Missing
    HbondPlan = _Missing
    RdfPlan = _Missing
    EndToEndPlan = _Missing
    ContourLengthPlan = _Missing
    ChainRgPlan = _Missing
    BondLengthDistributionPlan = _Missing
    BondAngleDistributionPlan = _Missing
    PersistenceLengthPlan = _Missing
from .builder import (
    charges_from_selections,
    charges_from_table,
    group_indices,
    group_types_from_selections,
)

__all__ = [
    "System",
    "Selection",
    "Trajectory",
    "RgPlan",
    "RmsdPlan",
    "MsdPlan",
    "RotAcfPlan",
    "ConductivityPlan",
    "DielectricPlan",
    "DipoleAlignmentPlan",
    "IonPairCorrelationPlan",
    "StructureFactorPlan",
    "WaterCountPlan",
    "EquipartitionPlan",
    "HbondPlan",
    "RdfPlan",
    "EndToEndPlan",
    "ContourLengthPlan",
    "ChainRgPlan",
    "BondLengthDistributionPlan",
    "BondAngleDistributionPlan",
    "PersistenceLengthPlan",
    "group_indices",
    "group_types_from_selections",
    "charges_from_selections",
    "charges_from_table",
]
