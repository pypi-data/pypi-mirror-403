//! PolyDup Python bindings via PyO3
//!
//! Performance optimization: Releases the GIL during compute-intensive operations
//! to allow concurrent Python code execution.
//!
//! # Example
//! ```python
//! import polydup
//!
//! report = polydup.find_duplicates(['./src', './lib'], min_block_size=50, threshold=0.85)

// Allow useless_conversion for PyResult types (PyO3 0.22 type inference improvement)
#![allow(clippy::useless_conversion)]
//! print(f"Found {len(report['duplicates'])} duplicates")
//! print(f"Scanned {report['files_scanned']} files in {report['stats']['duration_ms']}ms")
//! ```

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::path::PathBuf;

/// Represents a duplicate match found by the scanner
#[pyclass]
#[derive(Clone)]
pub struct DuplicateMatch {
    #[pyo3(get)]
    pub file1: String,
    #[pyo3(get)]
    pub file2: String,
    #[pyo3(get)]
    pub start_line1: usize,
    #[pyo3(get)]
    pub start_line2: usize,
    #[pyo3(get)]
    pub length: usize,
    #[pyo3(get)]
    pub similarity: f64,
    #[pyo3(get)]
    pub hash: String,
    #[pyo3(get)]
    pub clone_type: String,
    #[pyo3(get)]
    pub edit_distance: Option<usize>,
}

#[pymethods]
impl DuplicateMatch {
    fn __repr__(&self) -> String {
        format!(
            "DuplicateMatch(file1='{}', file2='{}', type={}, similarity={:.2})",
            self.file1, self.file2, self.clone_type, self.similarity
        )
    }

    fn __str__(&self) -> String {
        format!(
            "{} ↔️ {} ({:.1}% similar)",
            self.file1,
            self.file2,
            self.similarity * 100.0
        )
    }

    /// Convert to Python dictionary
    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new_bound(py);
        dict.set_item("file1", &self.file1)?;
        dict.set_item("file2", &self.file2)?;
        dict.set_item("start_line1", self.start_line1)?;
        dict.set_item("start_line2", self.start_line2)?;
        dict.set_item("length", self.length)?;
        dict.set_item("similarity", self.similarity)?;
        dict.set_item("hash", &self.hash)?;
        dict.set_item("clone_type", &self.clone_type)?;
        if let Some(edit_dist) = self.edit_distance {
            dict.set_item("edit_distance", edit_dist)?;
        }
        Ok(dict.into())
    }
}

/// Scan statistics
#[pyclass]
#[derive(Clone)]
pub struct ScanStats {
    #[pyo3(get)]
    pub total_lines: usize,
    #[pyo3(get)]
    pub total_tokens: usize,
    #[pyo3(get)]
    pub unique_hashes: usize,
    #[pyo3(get)]
    pub duration_ms: u64,
}

#[pymethods]
impl ScanStats {
    fn __repr__(&self) -> String {
        format!(
            "ScanStats(tokens={}, hashes={}, duration={}ms)",
            self.total_tokens, self.unique_hashes, self.duration_ms
        )
    }

    /// Convert to Python dictionary
    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new_bound(py);
        dict.set_item("total_lines", self.total_lines)?;
        dict.set_item("total_tokens", self.total_tokens)?;
        dict.set_item("unique_hashes", self.unique_hashes)?;
        dict.set_item("duration_ms", self.duration_ms)?;
        Ok(dict.into())
    }
}

/// Complete scan report as a PyClass
#[pyclass]
#[derive(Clone)]
pub struct Report {
    #[pyo3(get)]
    pub files_scanned: usize,
    #[pyo3(get)]
    pub functions_analyzed: usize,
    #[pyo3(get)]
    pub duplicates: Vec<DuplicateMatch>,
    #[pyo3(get)]
    pub stats: ScanStats,
}

#[pymethods]
impl Report {
    fn __repr__(&self) -> String {
        format!(
            "Report(files={}, functions={}, duplicates={})",
            self.files_scanned,
            self.functions_analyzed,
            self.duplicates.len()
        )
    }

    /// Convert to Python dictionary
    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new_bound(py);
        dict.set_item("files_scanned", self.files_scanned)?;
        dict.set_item("functions_analyzed", self.functions_analyzed)?;

        // Convert duplicates to list of dicts
        let dups: Vec<PyObject> = self
            .duplicates
            .iter()
            .map(|d| d.to_dict(py))
            .collect::<PyResult<Vec<_>>>()?;
        dict.set_item("duplicates", dups)?;

        dict.set_item("stats", self.stats.to_dict(py)?)?;
        Ok(dict.into())
    }

    /// Get number of duplicates
    fn __len__(&self) -> usize {
        self.duplicates.len()
    }
}

/// Convert dupe_core types to Python types
impl From<dupe_core::DuplicateMatch> for DuplicateMatch {
    fn from(m: dupe_core::DuplicateMatch) -> Self {
        Self {
            file1: m.file1,
            file2: m.file2,
            start_line1: m.start_line1,
            start_line2: m.start_line2,
            length: m.length,
            similarity: m.similarity,
            hash: format!("{:#x}", m.hash),
            clone_type: match m.clone_type {
                dupe_core::CloneType::Type1 => "type-1".to_string(),
                dupe_core::CloneType::Type2 => "type-2".to_string(),
                dupe_core::CloneType::Type3 => "type-3".to_string(),
            },
            edit_distance: m.edit_distance,
        }
    }
}

impl From<dupe_core::ScanStats> for ScanStats {
    fn from(s: dupe_core::ScanStats) -> Self {
        Self {
            total_lines: s.total_lines,
            total_tokens: s.total_tokens,
            unique_hashes: s.unique_hashes,
            duration_ms: s.duration_ms,
        }
    }
}

impl From<dupe_core::Report> for Report {
    fn from(r: dupe_core::Report) -> Self {
        Self {
            files_scanned: r.files_scanned,
            functions_analyzed: r.functions_analyzed,
            duplicates: r.duplicates.into_iter().map(DuplicateMatch::from).collect(),
            stats: ScanStats::from(r.stats),
        }
    }
}

/// Find duplicate code across multiple files
///
/// **CRITICAL**: This function releases the GIL during the scan operation,
/// allowing other Python threads to run concurrently. This is essential for
/// performance in multi-threaded Python applications.
///
/// Args:
///     paths (list[str]): List of file or directory paths to scan
///     min_block_size (int, optional): Minimum code block size in tokens. Defaults to 50.
///     threshold (float, optional): Similarity threshold 0.0-1.0. Defaults to 0.85.
///
/// Returns:
///     Report: Scan report containing duplicates and statistics
///
/// Raises:
///     RuntimeError: If scanning fails
///
/// Example:
///     >>> import polydup
///     >>> report = polydup.find_duplicates(['./src'], min_block_size=30, threshold=0.9)
///     >>> print(f"Found {len(report.duplicates)} duplicates")
///     >>> for dup in report.duplicates:
///     ...     print(f"{dup.file1} ↔️ {dup.file2}")
#[pyfunction]
#[pyo3(signature = (paths, min_block_size=50, threshold=0.85, enable_type3=false, type3_tolerance=0.85))]
fn find_duplicates(
    py: Python,
    paths: Vec<String>,
    min_block_size: usize,
    threshold: f64,
    enable_type3: bool,
    type3_tolerance: f64,
) -> PyResult<Report> {
    // Convert paths to PathBuf
    let path_bufs: Vec<PathBuf> = paths.iter().map(PathBuf::from).collect();

    // Create scanner
    let mut scanner = dupe_core::Scanner::with_config(min_block_size, threshold).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to create scanner: {}",
            e
        ))
    })?;

    // Enable Type-3 detection if requested
    if enable_type3 {
        scanner = scanner.with_type3_detection(type3_tolerance).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Invalid Type-3 tolerance: {}",
                e
            ))
        })?;
    }

    // CRITICAL: Release the GIL before CPU-intensive operation
    // This allows other Python threads to run while we're scanning
    let report = py.allow_threads(|| scanner.scan(path_bufs)).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Scan failed: {}", e))
    })?;

    // Convert to Python Report type
    Ok(Report::from(report))
}

/// Find duplicate code and return as Python dictionary
///
/// Same as find_duplicates() but returns a Python dict instead of a Report object.
/// This is useful for JSON serialization or when you prefer working with dicts.
///
/// **CRITICAL**: Also releases the GIL during scan operation.
///
/// Args:
///     paths (list[str]): List of file or directory paths to scan
///     min_block_size (int, optional): Minimum code block size in tokens. Defaults to 50.
///     threshold (float, optional): Similarity threshold 0.0-1.0. Defaults to 0.85.
///
/// Returns:
///     dict: Dictionary with keys: 'files_scanned', 'functions_analyzed', 'duplicates', 'stats'
///
/// Example:
///     >>> import polydup
///     >>> import json
///     >>> report_dict = polydup.find_duplicates_dict(['./src'])
///     >>> print(json.dumps(report_dict, indent=2))
#[pyfunction]
#[pyo3(signature = (paths, min_block_size=50, threshold=0.85, enable_type3=false, type3_tolerance=0.85))]
fn find_duplicates_dict(
    py: Python,
    paths: Vec<String>,
    min_block_size: usize,
    threshold: f64,
    enable_type3: bool,
    type3_tolerance: f64,
) -> PyResult<PyObject> {
    let report = find_duplicates(
        py,
        paths,
        min_block_size,
        threshold,
        enable_type3,
        type3_tolerance,
    )?;
    report.to_dict(py)
}

/// Get the version of the PolyDup library
///
/// Returns:
///     str: Version string
#[pyfunction]
fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// PolyDup - Cross-language duplicate code detector
///
/// This module provides Python bindings to the PolyDup Rust library for detecting
/// duplicate code across Rust, Python, and JavaScript/TypeScript codebases.
///
/// Key Features:
/// - Multi-language support (Rust, Python, JavaScript/TypeScript)
/// - Type-2 clone detection (structurally similar code)
/// - Parallel processing with Rayon
/// - GIL-free scanning for better Python concurrency
///
/// Functions:
///     find_duplicates(paths, min_block_size=50, threshold=0.85) -> Report
///     find_duplicates_dict(paths, min_block_size=50, threshold=0.85) -> dict
///     version() -> str
///
/// Classes:
///     Report: Scan results with statistics
///     DuplicateMatch: Individual duplicate match
///     ScanStats: Scan performance metrics
#[pymodule]
fn polydup(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_duplicates, m)?)?;
    m.add_function(wrap_pyfunction!(find_duplicates_dict, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_class::<Report>()?;
    m.add_class::<DuplicateMatch>()?;
    m.add_class::<ScanStats>()?;
    Ok(())
}
