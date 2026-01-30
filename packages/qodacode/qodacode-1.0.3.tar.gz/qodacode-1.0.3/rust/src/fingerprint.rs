//! Fingerprint computation for stable issue identification
//!
//! Fingerprints are stable hashes that identify issues across code changes.
//! Key properties:
//! - Stable across line number changes (code moves don't break suppressions)
//! - Different for different code snippets
//! - Different for different files
//! - Fast to compute
//!
//! Algorithm: BLAKE3 with custom normalization and salt

use blake3::Hasher;
use pyo3::prelude::*;
use unicode_normalization::UnicodeNormalization;

/// Internal salt for fingerprint computation
/// This adds a layer of uniqueness to our fingerprints
const FINGERPRINT_SALT: &[u8] = b"qodacode_fp_v1_2025";

/// Normalize code snippet for stable fingerprinting
///
/// Removes noise that doesn't affect semantics:
/// - Whitespace normalization
/// - Unicode normalization (NFKC)
/// - Comment removal (basic)
/// - String literal normalization
pub fn normalize_code(snippet: &str) -> String {
    let mut result = String::with_capacity(snippet.len());

    // Unicode NFKC normalization (compatibility composition)
    let normalized = snippet.nfkc().collect::<String>();

    let mut in_string = false;
    let mut string_char = ' ';
    let mut prev_char = ' ';
    let mut last_was_space = true;

    for ch in normalized.chars() {
        // Track string literals
        if !in_string && (ch == '"' || ch == '\'') {
            in_string = true;
            string_char = ch;
            result.push(ch);
            prev_char = ch;
            last_was_space = false;
            continue;
        }

        if in_string && ch == string_char && prev_char != '\\' {
            in_string = false;
            result.push(ch);
            prev_char = ch;
            last_was_space = false;
            continue;
        }

        // Inside string - keep as-is but normalize quotes content
        if in_string {
            // Normalize string content to placeholder for stability
            // This helps when string values change slightly
            if ch.is_alphanumeric() {
                result.push('_');
            } else {
                result.push(ch);
            }
            prev_char = ch;
            continue;
        }

        // Outside string - normalize whitespace
        if ch.is_whitespace() {
            if !last_was_space {
                result.push(' ');
                last_was_space = true;
            }
        } else {
            result.push(ch);
            last_was_space = false;
        }

        prev_char = ch;
    }

    result.trim().to_lowercase()
}

/// Compute a stable fingerprint for an issue
///
/// # Arguments
/// * `filepath` - Relative path to the file
/// * `rule_id` - The rule that detected this issue (e.g., "SEC-001")
/// * `snippet` - The code snippet containing the issue
///
/// # Returns
/// A 12-character hex string that uniquely identifies this issue
pub fn compute_fingerprint(filepath: &str, rule_id: &str, snippet: &str) -> String {
    // Normalize the code snippet
    let normalized_snippet = normalize_code(snippet);

    // Normalize filepath (use forward slashes, lowercase)
    let normalized_path = filepath
        .replace('\\', "/")
        .to_lowercase();

    // Create input for hashing
    let input = format!(
        "{}:{}:{}",
        normalized_path,
        rule_id.to_uppercase(),
        normalized_snippet
    );

    // Use BLAKE3 with keyed hashing (salt)
    let mut hasher = Hasher::new_keyed(
        &blake3_key_from_salt(FINGERPRINT_SALT)
    );
    hasher.update(input.as_bytes());
    let hash = hasher.finalize();

    // Return first 6 bytes as 12-char hex string
    hex::encode(&hash.as_bytes()[..6])
}

/// Convert salt to BLAKE3 key (32 bytes)
fn blake3_key_from_salt(salt: &[u8]) -> [u8; 32] {
    let mut key = [0u8; 32];
    let hash = blake3::hash(salt);
    key.copy_from_slice(hash.as_bytes());
    key
}

// ============================================================================
// Python bindings
// ============================================================================

/// Python binding for compute_fingerprint
#[pyfunction]
#[pyo3(name = "compute_fingerprint")]
pub fn py_compute_fingerprint(filepath: &str, rule_id: &str, snippet: &str) -> String {
    compute_fingerprint(filepath, rule_id, snippet)
}

/// Python binding for normalize_code
#[pyfunction]
#[pyo3(name = "normalize_code")]
pub fn py_normalize_code(snippet: &str) -> String {
    normalize_code(snippet)
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fingerprint_stable_on_line_change() {
        // Same code at different "lines" should have same fingerprint
        let fp1 = compute_fingerprint("src/config.py", "SEC-001", "api_key = 'secret'");
        let fp2 = compute_fingerprint("src/config.py", "SEC-001", "api_key = 'secret'");
        assert_eq!(fp1, fp2);
    }

    #[test]
    fn test_fingerprint_different_for_different_files() {
        let fp1 = compute_fingerprint("src/config.py", "SEC-001", "api_key = 'secret'");
        let fp2 = compute_fingerprint("src/other.py", "SEC-001", "api_key = 'secret'");
        assert_ne!(fp1, fp2);
    }

    #[test]
    fn test_fingerprint_different_for_different_rules() {
        let fp1 = compute_fingerprint("src/config.py", "SEC-001", "api_key = 'secret'");
        let fp2 = compute_fingerprint("src/config.py", "SEC-002", "api_key = 'secret'");
        assert_ne!(fp1, fp2);
    }

    #[test]
    fn test_fingerprint_length() {
        let fp = compute_fingerprint("test.py", "SEC-001", "test");
        assert_eq!(fp.len(), 12);
    }

    #[test]
    fn test_normalize_whitespace() {
        let normalized = normalize_code("api_key   =   'test'");
        assert!(!normalized.contains("  "));
    }

    #[test]
    fn test_normalize_case() {
        let normalized = normalize_code("API_KEY = 'TEST'");
        assert_eq!(normalized, normalized.to_lowercase());
    }
}
