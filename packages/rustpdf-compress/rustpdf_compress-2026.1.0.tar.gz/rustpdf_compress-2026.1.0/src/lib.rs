mod pdf;
mod web;

use pyo3::prelude::*;
use pyo3::types::PyBytes;

pub use pdf::{CompressionLevel, PdfCompressor};
pub use web::create_router;

/// Compress a PDF file with the specified compression level.
///
/// Args:
///     data: PDF file content as bytes
///     level: Compression level - "extreme", "recommended", or "low"
///
/// Returns:
///     Compressed PDF content as bytes
#[pyfunction]
#[pyo3(signature = (data, level="recommended"))]
fn compress(py: Python<'_>, data: &[u8], level: &str) -> PyResult<Py<PyBytes>> {
    let compression_level = match level {
        "extreme" => CompressionLevel::Extreme,
        "recommended" => CompressionLevel::Recommended,
        "low" => CompressionLevel::Low,
        _ => CompressionLevel::Recommended,
    };

    let compressor = PdfCompressor::new(compression_level);
    match compressor.compress(data) {
        Ok(compressed) => Ok(PyBytes::new_bound(py, &compressed).unbind()),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
    }
}

/// Compress a PDF file from path.
///
/// Args:
///     input_path: Path to input PDF file
///     output_path: Path to save compressed PDF
///     level: Compression level - "extreme", "recommended", or "low"
///
/// Returns:
///     Dictionary with compression statistics
#[pyfunction]
#[pyo3(signature = (input_path, output_path, level="recommended"))]
fn compress_file(input_path: &str, output_path: &str, level: &str) -> PyResult<(usize, usize, f64)> {
    let compression_level = match level {
        "extreme" => CompressionLevel::Extreme,
        "recommended" => CompressionLevel::Recommended,
        "low" => CompressionLevel::Low,
        _ => CompressionLevel::Recommended,
    };

    // Read input file
    let data = std::fs::read(input_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to read file: {}", e)))?;

    let original_size = data.len();

    // Compress
    let compressor = PdfCompressor::new(compression_level);
    let compressed = compressor
        .compress(&data)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;

    let compressed_size = compressed.len();

    // Write output file
    std::fs::write(output_path, &compressed)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to write file: {}", e)))?;

    let reduction = (1.0 - compressed_size as f64 / original_size as f64) * 100.0;

    Ok((original_size, compressed_size, reduction))
}

/// Python module for PDF compression.
#[pymodule]
fn rustpdf_compress(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compress, m)?)?;
    m.add_function(wrap_pyfunction!(compress_file, m)?)?;
    m.add("__version__", "2026.1.0")?;
    Ok(())
}
