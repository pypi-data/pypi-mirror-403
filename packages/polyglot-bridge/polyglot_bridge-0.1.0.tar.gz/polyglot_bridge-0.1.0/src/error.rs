use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::PyErr;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum BridgeError {
    #[error("Input cannot be empty")]
    EmptyInput,
    
    #[error("Computation resulted in overflow")]
    Overflow,
    
    #[error("Matrix dimensions do not match")]
    DimensionMismatch,
    
    #[error("Invalid type: {0}")]
    InvalidType(String),
    
    #[error("Computation error: {0}")]
    ComputationError(String),
}

impl From<BridgeError> for PyErr {
    fn from(err: BridgeError) -> PyErr {
        match err {
            BridgeError::InvalidType(_) => PyTypeError::new_err(err.to_string()),
            BridgeError::EmptyInput | BridgeError::DimensionMismatch => {
                PyValueError::new_err(err.to_string())
            }
            _ => PyRuntimeError::new_err(err.to_string()),
        }
    }
}
