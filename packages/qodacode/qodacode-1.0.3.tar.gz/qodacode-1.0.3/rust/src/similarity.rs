//! String similarity algorithms for typosquatting detection
//!
//! This module provides optimized implementations of:
//! - Levenshtein distance (edit distance)
//! - Homoglyph detection (Unicode lookalikes)
//! - Keyboard proximity scoring (QWERTY adjacency)
//! - Combined similarity scoring
//!
//! These algorithms are critical for detecting supply chain attacks.

use pyo3::prelude::*;
use std::collections::HashMap;

// ============================================================================
// Homoglyph mappings (Unicode lookalikes)
// This is proprietary data - compiled into binary
// ============================================================================

lazy_static::lazy_static! {
    /// Homoglyph mapping: character -> list of lookalikes
    static ref HOMOGLYPHS: HashMap<char, Vec<char>> = {
        let mut m = HashMap::new();
        // Latin -> Cyrillic/Greek lookalikes
        m.insert('a', vec!['а', 'ɑ', 'α', 'ａ']); // Cyrillic а, Latin ɑ, Greek α
        m.insert('c', vec!['с', 'ϲ', 'ｃ']);       // Cyrillic с
        m.insert('e', vec!['е', 'ё', 'ε', 'ｅ']);   // Cyrillic е, Greek ε
        m.insert('o', vec!['о', 'ο', '0', 'ｏ']);   // Cyrillic о, Greek ο, digit 0
        m.insert('p', vec!['р', 'ρ', 'ｐ']);       // Cyrillic р, Greek ρ
        m.insert('s', vec!['ѕ', 'ｓ']);            // Cyrillic ѕ
        m.insert('x', vec!['х', 'ｘ']);            // Cyrillic х
        m.insert('y', vec!['у', 'ｙ']);            // Cyrillic у
        m.insert('i', vec!['і', 'ι', '1', 'l', 'ｉ']); // Cyrillic і, Greek ι
        m.insert('l', vec!['1', 'I', '|', 'ｌ']);
        m.insert('n', vec!['п', 'ｎ']);            // Cyrillic п (looks like n in some fonts)
        m.insert('u', vec!['υ', 'ｕ']);            // Greek υ
        m.insert('v', vec!['ν', 'ｖ']);            // Greek ν
        m.insert('w', vec!['ω', 'ｗ']);            // Greek ω
        m.insert('k', vec!['κ', 'ｋ']);            // Greek κ
        m.insert('t', vec!['τ', 'ｔ']);            // Greek τ
        m.insert('h', vec!['һ', 'ｈ']);            // Cyrillic һ
        m.insert('d', vec!['ԁ', 'ｄ']);            // Cyrillic ԁ
        m.insert('g', vec!['ɡ', 'ｇ']);            // Latin ɡ
        m.insert('q', vec!['ԛ', 'ｑ']);            // Cyrillic ԛ
        m.insert('r', vec!['г', 'ｒ']);            // Cyrillic г (partial)
        m.insert('m', vec!['м', 'ｍ']);            // Cyrillic м
        m.insert('b', vec!['Ь', 'ｂ']);            // Cyrillic Ь (soft sign)
        m.insert('f', vec!['ｆ']);
        m.insert('j', vec!['ј', 'ｊ']);            // Cyrillic ј
        m.insert('z', vec!['ｚ']);
        m
    };

    /// Reverse homoglyph mapping: lookalike -> original
    static ref HOMOGLYPHS_REVERSE: HashMap<char, char> = {
        let mut m = HashMap::new();
        for (original, lookalikes) in HOMOGLYPHS.iter() {
            for lookalike in lookalikes {
                m.insert(*lookalike, *original);
            }
        }
        m
    };

    /// QWERTY keyboard adjacency map
    static ref QWERTY_ADJACENT: HashMap<char, Vec<char>> = {
        let mut m = HashMap::new();
        m.insert('q', vec!['w', 'a', '1', '2']);
        m.insert('w', vec!['q', 'e', 'a', 's', '2', '3']);
        m.insert('e', vec!['w', 'r', 's', 'd', '3', '4']);
        m.insert('r', vec!['e', 't', 'd', 'f', '4', '5']);
        m.insert('t', vec!['r', 'y', 'f', 'g', '5', '6']);
        m.insert('y', vec!['t', 'u', 'g', 'h', '6', '7']);
        m.insert('u', vec!['y', 'i', 'h', 'j', '7', '8']);
        m.insert('i', vec!['u', 'o', 'j', 'k', '8', '9']);
        m.insert('o', vec!['i', 'p', 'k', 'l', '9', '0']);
        m.insert('p', vec!['o', 'l', '0', '-']);
        m.insert('a', vec!['q', 'w', 's', 'z']);
        m.insert('s', vec!['a', 'w', 'e', 'd', 'z', 'x']);
        m.insert('d', vec!['s', 'e', 'r', 'f', 'x', 'c']);
        m.insert('f', vec!['d', 'r', 't', 'g', 'c', 'v']);
        m.insert('g', vec!['f', 't', 'y', 'h', 'v', 'b']);
        m.insert('h', vec!['g', 'y', 'u', 'j', 'b', 'n']);
        m.insert('j', vec!['h', 'u', 'i', 'k', 'n', 'm']);
        m.insert('k', vec!['j', 'i', 'o', 'l', 'm']);
        m.insert('l', vec!['k', 'o', 'p']);
        m.insert('z', vec!['a', 's', 'x']);
        m.insert('x', vec!['z', 's', 'd', 'c']);
        m.insert('c', vec!['x', 'd', 'f', 'v']);
        m.insert('v', vec!['c', 'f', 'g', 'b']);
        m.insert('b', vec!['v', 'g', 'h', 'n']);
        m.insert('n', vec!['b', 'h', 'j', 'm']);
        m.insert('m', vec!['n', 'j', 'k']);
        m
    };
}

// ============================================================================
// Levenshtein Distance
// ============================================================================

/// Compute Levenshtein (edit) distance between two strings
///
/// Uses optimized single-row dynamic programming approach.
pub fn levenshtein_distance(s1: &str, s2: &str) -> usize {
    let s1_chars: Vec<char> = s1.chars().collect();
    let s2_chars: Vec<char> = s2.chars().collect();

    let len1 = s1_chars.len();
    let len2 = s2_chars.len();

    // Early exit for empty strings
    if len1 == 0 {
        return len2;
    }
    if len2 == 0 {
        return len1;
    }

    // Single-row optimization
    let mut prev_row: Vec<usize> = (0..=len2).collect();
    let mut curr_row: Vec<usize> = vec![0; len2 + 1];

    for i in 1..=len1 {
        curr_row[0] = i;

        for j in 1..=len2 {
            let cost = if s1_chars[i - 1] == s2_chars[j - 1] {
                0
            } else {
                1
            };

            curr_row[j] = (prev_row[j] + 1)
                .min(curr_row[j - 1] + 1)
                .min(prev_row[j - 1] + cost);
        }

        std::mem::swap(&mut prev_row, &mut curr_row);
    }

    prev_row[len2]
}

// ============================================================================
// Homoglyph Detection
// ============================================================================

/// Check if a string contains homoglyph characters
pub fn contains_homoglyphs(s: &str) -> bool {
    s.chars().any(|c| HOMOGLYPHS_REVERSE.contains_key(&c))
}

/// Normalize a string by replacing homoglyphs with their ASCII equivalents
pub fn normalize_homoglyphs(s: &str) -> String {
    s.chars()
        .map(|c| *HOMOGLYPHS_REVERSE.get(&c).unwrap_or(&c))
        .collect()
}

/// Check if two strings are homoglyph variants of each other
pub fn is_homoglyph_attack(suspicious: &str, legitimate: &str) -> bool {
    if suspicious == legitimate {
        return false;
    }

    let normalized_suspicious = normalize_homoglyphs(suspicious);
    let normalized_legitimate = normalize_homoglyphs(legitimate);

    // After normalization, they should be identical or very close
    normalized_suspicious == normalized_legitimate
        || levenshtein_distance(&normalized_suspicious, &normalized_legitimate) <= 1
}

// ============================================================================
// Keyboard Proximity
// ============================================================================

/// Check if two characters are adjacent on QWERTY keyboard
pub fn are_adjacent(c1: char, c2: char) -> bool {
    let c1_lower = c1.to_ascii_lowercase();
    let c2_lower = c2.to_ascii_lowercase();

    QWERTY_ADJACENT
        .get(&c1_lower)
        .map(|adj| adj.contains(&c2_lower))
        .unwrap_or(false)
}

/// Compute keyboard distance between two strings
/// Returns the number of character pairs that differ by keyboard adjacency
pub fn keyboard_distance(s1: &str, s2: &str) -> usize {
    if s1.len() != s2.len() {
        return usize::MAX;
    }

    s1.chars()
        .zip(s2.chars())
        .filter(|(c1, c2)| c1 != c2 && are_adjacent(*c1, *c2))
        .count()
}

// ============================================================================
// Combined Similarity Score
// ============================================================================

/// Compute comprehensive similarity score between package names
///
/// Returns a score from 0.0 to 1.0 where:
/// - 1.0 = definitely a typosquatting attempt
/// - 0.0 = no similarity
///
/// Factors considered:
/// - Edit distance
/// - Homoglyph presence
/// - Keyboard proximity
/// - String length ratio
pub fn compute_similarity_score(suspicious: &str, legitimate: &str) -> f64 {
    // Exact match = not suspicious (legitimate package)
    if suspicious == legitimate {
        return 0.0;
    }

    let s1 = suspicious.to_lowercase();
    let s2 = legitimate.to_lowercase();

    // Homoglyph attack = very high score
    if is_homoglyph_attack(&s1, &s2) {
        return 0.95;
    }

    // Edit distance
    let edit_dist = levenshtein_distance(&s1, &s2);
    let max_len = s1.len().max(s2.len());

    // Too different = not suspicious
    if edit_dist > 3 || (edit_dist as f64 / max_len as f64) > 0.4 {
        return 0.0;
    }

    // Base score from edit distance
    let edit_score = 1.0 - (edit_dist as f64 / max_len as f64);

    // Keyboard proximity bonus
    let keyboard_dist = keyboard_distance(&s1, &s2);
    let keyboard_bonus = if keyboard_dist > 0 && keyboard_dist <= 2 {
        0.15 * (keyboard_dist as f64 / 2.0)
    } else {
        0.0
    };

    // Length similarity bonus
    let len_ratio = s1.len().min(s2.len()) as f64 / s1.len().max(s2.len()) as f64;
    let len_bonus = if len_ratio > 0.8 { 0.1 } else { 0.0 };

    // Combine scores
    let final_score = (edit_score * 0.7 + keyboard_bonus + len_bonus).min(1.0);

    // Only return scores above threshold
    if final_score >= 0.5 {
        final_score
    } else {
        0.0
    }
}

// ============================================================================
// Python bindings
// ============================================================================

#[pyfunction]
#[pyo3(name = "levenshtein_distance")]
pub fn py_levenshtein_distance(s1: &str, s2: &str) -> usize {
    levenshtein_distance(s1, s2)
}

#[pyfunction]
#[pyo3(name = "compute_similarity_score")]
pub fn py_compute_similarity_score(suspicious: &str, legitimate: &str) -> f64 {
    compute_similarity_score(suspicious, legitimate)
}

#[pyfunction]
#[pyo3(name = "is_homoglyph_attack")]
pub fn py_is_homoglyph_attack(suspicious: &str, legitimate: &str) -> bool {
    is_homoglyph_attack(suspicious, legitimate)
}

#[pyfunction]
#[pyo3(name = "keyboard_distance")]
pub fn py_keyboard_distance(s1: &str, s2: &str) -> usize {
    keyboard_distance(s1, s2)
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_levenshtein_basic() {
        assert_eq!(levenshtein_distance("kitten", "sitting"), 3);
        assert_eq!(levenshtein_distance("", "abc"), 3);
        assert_eq!(levenshtein_distance("abc", ""), 3);
        assert_eq!(levenshtein_distance("abc", "abc"), 0);
    }

    #[test]
    fn test_levenshtein_typosquat() {
        assert_eq!(levenshtein_distance("requests", "reqeusts"), 2);
        assert_eq!(levenshtein_distance("colorama", "colourama"), 1);
    }

    #[test]
    fn test_homoglyph_detection() {
        assert!(contains_homoglyphs("rеquests")); // Cyrillic е
        assert!(!contains_homoglyphs("requests"));
    }

    #[test]
    fn test_homoglyph_attack() {
        assert!(is_homoglyph_attack("rеquests", "requests")); // Cyrillic е
        assert!(!is_homoglyph_attack("requests", "requests"));
    }

    #[test]
    fn test_keyboard_adjacent() {
        assert!(are_adjacent('q', 'w'));
        assert!(are_adjacent('a', 's'));
        assert!(!are_adjacent('q', 'p'));
    }

    #[test]
    fn test_similarity_score() {
        // Typosquat should have high score
        let score = compute_similarity_score("reqeusts", "requests");
        assert!(score >= 0.5);

        // Completely different = 0
        let score = compute_similarity_score("numpy", "django");
        assert_eq!(score, 0.0);

        // Same = 0 (not suspicious)
        let score = compute_similarity_score("requests", "requests");
        assert_eq!(score, 0.0);
    }
}
