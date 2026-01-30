"""
Similarity algorithms for typosquatting detection.

Implements multiple detection strategies:
1. Levenshtein distance - Edit distance between strings
2. Homoglyph detection - Visually similar characters
3. Keyboard proximity - Adjacent keys on keyboard
"""

from typing import Dict, List, Set, Tuple


# Homoglyph mappings - characters that look similar
HOMOGLYPHS: Dict[str, Set[str]] = {
    "a": {"а", "ɑ", "α"},  # Cyrillic а, Latin alpha
    "e": {"е", "ε"},  # Cyrillic е
    "o": {"о", "ο", "0"},  # Cyrillic о, Greek omicron, zero
    "c": {"с", "ϲ"},  # Cyrillic с
    "p": {"р", "ρ"},  # Cyrillic р, Greek rho
    "x": {"х", "χ"},  # Cyrillic х, Greek chi
    "y": {"у", "γ"},  # Cyrillic у
    "i": {"і", "ι", "1", "l"},  # Ukrainian і, Greek iota, one, lowercase L
    "l": {"1", "I", "i", "|"},  # One, uppercase I, lowercase i
    "s": {"ѕ"},  # Cyrillic ѕ
    "d": {"ԁ"},  # Cyrillic ԁ
    "g": {"ɡ"},  # Latin small letter script g
    "n": {"п"},  # Cyrillic п (looks like n)
    "m": {"м"},  # Cyrillic м
    "t": {"τ"},  # Greek tau
    "u": {"υ", "ս"},  # Greek upsilon, Armenian u
    "w": {"ѡ", "ω"},  # Cyrillic omega
    "r": {"г"},  # Cyrillic г (looks like r rotated)
    "0": {"o", "O", "О"},  # Letters that look like zero
    "1": {"l", "I", "i"},  # Letters that look like one
}

# Keyboard layout for proximity detection (QWERTY)
KEYBOARD_ROWS = [
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
]

# Build adjacency map
KEYBOARD_ADJACENT: Dict[str, Set[str]] = {}
for row_idx, row in enumerate(KEYBOARD_ROWS):
    for col_idx, char in enumerate(row):
        adjacent = set()
        # Same row neighbors
        if col_idx > 0:
            adjacent.add(row[col_idx - 1])
        if col_idx < len(row) - 1:
            adjacent.add(row[col_idx + 1])
        # Adjacent rows (approximate - QWERTY has offset)
        if row_idx > 0:
            upper_row = KEYBOARD_ROWS[row_idx - 1]
            for offset in [-1, 0, 1]:
                idx = col_idx + offset
                if 0 <= idx < len(upper_row):
                    adjacent.add(upper_row[idx])
        if row_idx < len(KEYBOARD_ROWS) - 1:
            lower_row = KEYBOARD_ROWS[row_idx + 1]
            for offset in [-1, 0, 1]:
                idx = col_idx + offset
                if 0 <= idx < len(lower_row):
                    adjacent.add(lower_row[idx])
        KEYBOARD_ADJACENT[char] = adjacent


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.

    This is the minimum number of single-character edits (insertions,
    deletions, or substitutions) required to change one string into the other.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Integer edit distance

    Examples:
        >>> levenshtein_distance("requests", "reqeusts")
        2
        >>> levenshtein_distance("numpy", "numpyy")
        1
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost is 0 if characters match, 1 otherwise
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def detect_homoglyphs(package_name: str) -> List[Tuple[int, str, str]]:
    """
    Detect homoglyph characters in a package name.

    Returns positions and the suspicious character along with what it
    might be impersonating.

    Args:
        package_name: The package name to check

    Returns:
        List of (position, suspicious_char, likely_intended_char)

    Examples:
        >>> detect_homoglyphs("fIask")  # Capital I instead of lowercase l
        [(1, 'I', 'l')]
    """
    results = []

    # Build reverse mapping: suspicious char -> legitimate char
    reverse_map: Dict[str, str] = {}
    for legit, suspicious_set in HOMOGLYPHS.items():
        for sus in suspicious_set:
            reverse_map[sus] = legit

    for i, char in enumerate(package_name):
        if char in reverse_map:
            results.append((i, char, reverse_map[char]))

    return results


def keyboard_proximity_score(s1: str, s2: str) -> float:
    """
    Calculate how likely the difference between strings is due to keyboard typos.

    Higher score means more likely to be a typo (adjacent keys).

    Args:
        s1: First string (legitimate package)
        s2: Second string (suspicious package)

    Returns:
        Float score 0.0-1.0 where 1.0 means all differences are adjacent keys

    Examples:
        >>> keyboard_proximity_score("flask", "flsak")  # s and a are adjacent
        1.0
    """
    if len(s1) != len(s2):
        return 0.0

    differences = 0
    adjacent_differences = 0

    for c1, c2 in zip(s1, s2):
        if c1 != c2:
            differences += 1
            c1_lower = c1.lower()
            c2_lower = c2.lower()
            if c1_lower in KEYBOARD_ADJACENT and c2_lower in KEYBOARD_ADJACENT.get(c1_lower, set()):
                adjacent_differences += 1
            elif c2_lower in KEYBOARD_ADJACENT and c1_lower in KEYBOARD_ADJACENT.get(c2_lower, set()):
                adjacent_differences += 1

    if differences == 0:
        return 0.0

    return adjacent_differences / differences


def normalize_package_name(name: str) -> str:
    """
    Normalize a package name for comparison.

    - Lowercase
    - Replace underscores and dots with hyphens
    - Strip whitespace

    Args:
        name: Package name to normalize

    Returns:
        Normalized package name
    """
    return name.lower().replace("_", "-").replace(".", "-").strip()


def is_similar(pkg1: str, pkg2: str, threshold: int = 2) -> bool:
    """
    Check if two package names are suspiciously similar.

    Args:
        pkg1: First package name
        pkg2: Second package name
        threshold: Maximum Levenshtein distance to consider similar

    Returns:
        True if packages are similar enough to be suspicious
    """
    # Normalize both names
    n1 = normalize_package_name(pkg1)
    n2 = normalize_package_name(pkg2)

    # Exact match after normalization
    if n1 == n2:
        return False  # Same package, not typosquatting

    # Check Levenshtein distance
    distance = levenshtein_distance(n1, n2)
    if distance <= threshold:
        return True

    # Check for homoglyphs
    if detect_homoglyphs(pkg2):
        return True

    return False
