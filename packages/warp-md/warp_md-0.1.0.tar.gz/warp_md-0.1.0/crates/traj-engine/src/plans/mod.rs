pub mod rg;
pub mod rmsd;
pub mod rdf;
pub mod polymer;
pub mod analysis;

pub use rg::RgPlan;
pub use rmsd::RmsdPlan;
pub use rdf::RdfPlan;
pub use polymer::{
    BondAngleDistributionPlan, BondLengthDistributionPlan, ChainRgPlan,
    ContourLengthPlan, EndToEndPlan, PersistenceLengthPlan,
};
pub use analysis::{MsdPlan};

#[derive(Debug, Clone, Copy)]
pub enum ReferenceMode {
    Topology,
    Frame0,
}

#[derive(Debug, Clone, Copy)]
pub enum PbcMode {
    None,
    Orthorhombic,
}
