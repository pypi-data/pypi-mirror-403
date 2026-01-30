use thiserror::Error;


#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum PpuError {
    #[error("PPU does not match any known format: '{ppu}'.")]
    UnknownFormat { ppu: String },

    #[error("Expected length '{expected}', but got '{actual}' ('{chars}').")]
    InvalidLength { expected: usize, actual: usize, chars: String },

    #[error("Unknown letter: '{letter}'.")]
    UnknownLetter { letter: String },

    #[error("Letter cannot be empty.")]
    EmptyLetter,

    #[error("Unknown digraph: '{letters}'.")]
    UnknownDigraph { letters: String },

    #[error("Digraph cannot be empty.")]
    EmptyDigraph,
}


#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum VerifierError {
    #[error("Digits cannot be empty.")]
    EmptyDigits,

    #[error("Verifier cannot be empty.")]
    EmptyVerifier,

    #[error("Input must be only digits, but '{input}' was given.")]
    InvalidDigits { input: String },

    #[error("Verifier must be single '0'..'9' or 'K', but '{verifier}' was given.")]
    InvalidVerifier { verifier: String },

    #[error("Unexpected verifier computation.")]
    UnexpectedComputation,
}


#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum GenerateError{
    #[error("Invalid range: `min` '{min}' must be less than `max` '{max}'.")]
    InvalidRange { min: i32, max: i32 },

    #[error("{msg}")]
    InvalidInput { msg: String },

    #[error("Range too small to generate '{n}' unique RUTs: only '{range_size}' available.")]
    InsufficientRange { n: i32, range_size: i32 },

    #[error("Unexpected error during RUT generation: {0}")]
    UnexpectedGeneration(#[from] VerifierError),
}