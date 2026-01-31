#![forbid(unsafe_code)]

pub mod elements;
pub mod error;
pub mod frame;
pub mod interner;
pub mod selection;
pub mod system;

pub use error::{TrajError, TrajResult};
pub use frame::{Box3, FrameChunk, FrameChunkBuilder};
pub use interner::StringInterner;
pub use selection::Selection;
pub use system::{AtomTable, System};
