//! Pattern matching for safe code detection
//!
//! Uses Aho-Corasick algorithm for efficient multi-pattern matching.
//! This allows checking thousands of patterns in a single pass.

use aho_corasick::AhoCorasick;
use pyo3::prelude::*;
use regex::Regex;

lazy_static::lazy_static! {
    /// Safe patterns for secret detection false positive reduction
    static ref SAFE_SECRET_PATTERNS: Vec<(&'static str, &'static str)> = vec![
        // Environment variable reads
        (r"os\.environ", "Environment variable read"),
        (r"os\.getenv", "Environment variable read"),
        (r"process\.env\.", "Node.js environment read"),
        (r"import\.meta\.env\.", "Vite environment read"),
        (r"dotenv\.get", "Dotenv read"),
        (r"env\[", "Environment bracket access"),

        // Cryptographic operations (not hardcoded secrets)
        (r"decrypt", "Decryption operation"),
        (r"\.decrypt\(", "Decrypt method call"),
        (r"encrypt", "Encryption operation"),
        (r"hash", "Hash operation"),
        (r"bcrypt\.", "Bcrypt operation"),
        (r"argon2", "Argon2 operation"),
        (r"pbkdf2", "PBKDF2 operation"),
        (r"scrypt", "Scrypt operation"),
        (r"Fernet\(", "Fernet encryption"),
        (r"AES\.", "AES encryption"),
        (r"RSA\.", "RSA encryption"),

        // Configuration object reads
        (r"settings\.", "Settings object access"),
        (r"config\.", "Config object access"),
        (r"\.config\.", "Config property access"),
        (r"Config\.", "Config class access"),
        (r"Configuration\.", "Configuration class"),
        (r"AppSettings\.", "App settings access"),

        // Test/mock data indicators
        (r"mock_", "Mock data prefix"),
        (r"_mock", "Mock data suffix"),
        (r"fake_", "Fake data prefix"),
        (r"test_", "Test data prefix"),
        (r"dummy_", "Dummy data prefix"),
        (r"sample_", "Sample data prefix"),
        (r"example_", "Example data prefix"),

        // Placeholder patterns
        (r"<YOUR_", "Placeholder bracket"),
        (r"YOUR_.*_HERE", "Placeholder marker"),
        (r"\$\{", "Template variable"),
        (r"\{\{", "Template variable"),
        (r"xxx", "Placeholder xxx"),
        (r"XXX", "Placeholder XXX"),
        (r"changeme", "Placeholder changeme"),
        (r"CHANGEME", "Placeholder CHANGEME"),

        // Test database URLs
        (r"sqlite:///:memory:", "In-memory SQLite"),
        (r"localhost", "Localhost reference"),
        (r"127\.0\.0\.1", "Localhost IP"),
        (r"example\.com", "Example domain"),
        (r"example\.org", "Example domain"),
        (r"test\.com", "Test domain"),
    ];

    /// Compiled Aho-Corasick matcher for safe patterns
    static ref SAFE_PATTERN_MATCHER: AhoCorasick = {
        let patterns: Vec<&str> = SAFE_SECRET_PATTERNS
            .iter()
            .map(|(p, _)| *p)
            .collect();
        AhoCorasick::builder()
            .ascii_case_insensitive(true)
            .build(&patterns)
            .expect("Failed to build pattern matcher")
    };

    /// Test file path patterns
    static ref TEST_PATH_REGEX: Regex = Regex::new(
        r"(?i)(test[s_]?|spec[s_]?|__test__|__spec__|\bfixtures?\b|\bmocks?\b)"
    ).expect("Failed to compile test path regex");
}

/// Result of a safe pattern match
#[derive(Debug, Clone)]
pub struct SafeMatch {
    pub pattern: String,
    pub reason: String,
    pub position: usize,
}

/// Check if a code snippet matches any safe pattern
///
/// Returns Some(SafeMatch) if a safe pattern is found, None otherwise.
pub fn is_safe_pattern(snippet: &str, filepath: &str) -> Option<SafeMatch> {
    // Check if file is a test file
    if TEST_PATH_REGEX.is_match(filepath) {
        return Some(SafeMatch {
            pattern: "test_file".to_string(),
            reason: "Test file - likely test fixture".to_string(),
            position: 0,
        });
    }

    // Check against safe patterns using Aho-Corasick
    if let Some(mat) = SAFE_PATTERN_MATCHER.find(snippet) {
        let pattern_idx = mat.pattern().as_usize();
        let (pattern, reason) = SAFE_SECRET_PATTERNS[pattern_idx];
        return Some(SafeMatch {
            pattern: pattern.to_string(),
            reason: reason.to_string(),
            position: mat.start(),
        });
    }

    None
}

/// Match all patterns in a snippet and return all matches
pub fn match_patterns(snippet: &str) -> Vec<SafeMatch> {
    SAFE_PATTERN_MATCHER
        .find_iter(snippet)
        .map(|mat| {
            let pattern_idx = mat.pattern().as_usize();
            let (pattern, reason) = SAFE_SECRET_PATTERNS[pattern_idx];
            SafeMatch {
                pattern: pattern.to_string(),
                reason: reason.to_string(),
                position: mat.start(),
            }
        })
        .collect()
}

// ============================================================================
// Python bindings
// ============================================================================

/// Python binding for is_safe_pattern
/// Returns (is_safe, pattern, reason) tuple
#[pyfunction]
#[pyo3(name = "is_safe_pattern")]
pub fn py_is_safe_pattern(snippet: &str, filepath: &str) -> (bool, String, String) {
    match is_safe_pattern(snippet, filepath) {
        Some(m) => (true, m.pattern, m.reason),
        None => (false, String::new(), String::new()),
    }
}

/// Python binding for match_patterns
/// Returns list of (pattern, reason, position) tuples
#[pyfunction]
#[pyo3(name = "match_patterns")]
pub fn py_match_patterns(snippet: &str) -> Vec<(String, String, usize)> {
    match_patterns(snippet)
        .into_iter()
        .map(|m| (m.pattern, m.reason, m.position))
        .collect()
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_env_pattern() {
        let result = is_safe_pattern("api_key = os.environ['KEY']", "src/config.py");
        assert!(result.is_some());
        assert!(result.unwrap().reason.contains("Environment"));
    }

    #[test]
    fn test_decrypt_pattern() {
        let result = is_safe_pattern("secret = decrypt(data)", "src/crypto.py");
        assert!(result.is_some());
        assert!(result.unwrap().reason.contains("Decrypt"));
    }

    #[test]
    fn test_test_file() {
        let result = is_safe_pattern("password = 'test123'", "tests/test_auth.py");
        assert!(result.is_some());
        assert!(result.unwrap().reason.contains("test"));
    }

    #[test]
    fn test_placeholder() {
        let result = is_safe_pattern("api_key = '<YOUR_API_KEY>'", "src/config.py");
        assert!(result.is_some());
    }

    #[test]
    fn test_real_secret_not_safe() {
        let result = is_safe_pattern(
            "api_key = 'sk-ant-api03-AbCdEf123456789'",
            "src/production.py"
        );
        assert!(result.is_none());
    }

    #[test]
    fn test_match_multiple() {
        let matches = match_patterns("secret = os.environ.get('KEY') or decrypt(data)");
        assert!(matches.len() >= 2);
    }
}
