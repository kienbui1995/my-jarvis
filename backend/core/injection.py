"""Prompt injection detection — regex scanner, high-confidence blocks."""
import re

_PATTERNS = [
    (r"ignore\s+(previous|above|all)\s+instructions", 0.9),
    (r"you\s+are\s+now\s+(?:a|an)\s+", 0.7),
    (r"system\s*:\s*", 0.6),
    (r"<\|im_start\|>", 0.95),
    (r"```\s*system", 0.8),
    (r"ADMIN\s*OVERRIDE", 0.95),
]
_COMPILED = [(re.compile(p, re.IGNORECASE), s) for p, s in _PATTERNS]

# Score at or above this threshold will cause the request to be blocked
BLOCK_THRESHOLD = 0.8


def scan_injection(text: str) -> tuple[float, str | None]:
    """Scan text for injection patterns. Returns (score 0-1, matched_pattern or None)."""
    for pattern, score in _COMPILED:
        if pattern.search(text):
            return score, pattern.pattern
    return 0.0, None


def should_block(score: float) -> bool:
    """Return True if injection score is high enough to block the request."""
    return score >= BLOCK_THRESHOLD
