
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PpuFormat {
    LLLNN,
    LLLNNN,
    LLLLNN,
    LLNNNN,
}


impl PpuFormat {
    pub fn as_str(&self) -> &'static str {
        match self {
            PpuFormat::LLLNN => "LLLNN",
            PpuFormat::LLLNNN => "LLLNNN",
            PpuFormat::LLLLNN => "LLLLNN",
            PpuFormat::LLNNNN => "LLNNNN",
        }
    }
}