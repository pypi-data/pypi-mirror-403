"""
Typosquatting Detection Module.

Detects malicious packages with names similar to legitimate ones.
This is a key differentiator for Qodacode - creates defensible IP.
"""

from qodacode.typosquatting.detector import TyposquattingDetector, TyposquatMatch
from qodacode.typosquatting.similarity import (
    levenshtein_distance,
    detect_homoglyphs,
    keyboard_proximity_score,
)

__all__ = [
    "TyposquattingDetector",
    "TyposquatMatch",
    "levenshtein_distance",
    "detect_homoglyphs",
    "keyboard_proximity_score",
]
