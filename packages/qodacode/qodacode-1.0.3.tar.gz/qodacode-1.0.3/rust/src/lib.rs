//! Qodacode Core - High-performance algorithms for security scanning
//!
//! This module provides compiled, optimized implementations of:
//! - Fingerprint computation (stable issue hashing)
//! - String similarity (Levenshtein, homoglyphs, keyboard proximity)
//! - Pattern matching (Aho-Corasick multi-pattern)
//! - Embedded security data (typosquatting DB, secret patterns)
//!
//! These algorithms and data are intentionally compiled to prevent easy replication
//! while providing significant performance improvements over Python.

use pyo3::prelude::*;

mod fingerprint;
mod similarity;
mod patterns;
mod data;

// Re-export public functions
pub use fingerprint::compute_fingerprint;
pub use similarity::{levenshtein_distance, compute_similarity_score};
pub use patterns::is_safe_pattern;
pub use data::{is_known_malicious, is_legitimate_package, get_data_stats};

/// Qodacode Core Python Module
///
/// Exposes high-performance Rust functions to Python via PyO3.
#[pymodule]
fn qodacode_core(_py: Python, m: &PyModule) -> PyResult<()> {
    // Version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("RUST_CORE_AVAILABLE", true)?;

    // Fingerprint functions
    m.add_function(wrap_pyfunction!(fingerprint::py_compute_fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(fingerprint::py_normalize_code, m)?)?;

    // Similarity functions
    m.add_function(wrap_pyfunction!(similarity::py_levenshtein_distance, m)?)?;
    m.add_function(wrap_pyfunction!(similarity::py_compute_similarity_score, m)?)?;
    m.add_function(wrap_pyfunction!(similarity::py_is_homoglyph_attack, m)?)?;
    m.add_function(wrap_pyfunction!(similarity::py_keyboard_distance, m)?)?;

    // Pattern matching functions
    m.add_function(wrap_pyfunction!(patterns::py_is_safe_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(patterns::py_match_patterns, m)?)?;

    // Embedded data functions (Data Moats)
    m.add_function(wrap_pyfunction!(data::is_known_malicious, m)?)?;
    m.add_function(wrap_pyfunction!(data::is_legitimate_package, m)?)?;
    m.add_function(wrap_pyfunction!(data::get_known_malicious_packages, m)?)?;
    m.add_function(wrap_pyfunction!(data::get_data_stats, m)?)?;
    m.add_function(wrap_pyfunction!(data::get_legitimate_packages, m)?)?;
    m.add_function(wrap_pyfunction!(data::get_entropy_threshold, m)?)?;
    m.add_function(wrap_pyfunction!(data::matches_secret_prefix, m)?)?;
    m.add_function(wrap_pyfunction!(data::verify_data_integrity, m)?)?;

    Ok(())
}
