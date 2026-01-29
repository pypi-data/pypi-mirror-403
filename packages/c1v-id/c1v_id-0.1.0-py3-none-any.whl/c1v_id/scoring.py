"""
Similarity scoring functions for identity resolution.

These functions calculate how similar two records are, returning a score
between 0.0 (no match) and 1.0 (perfect match). The score determines
whether records should be auto-merged, flagged for review, or ignored.

Scoring approaches:
- exact_match: Binary yes/no for deterministic fields (email, phone)
- fuzzy_score: Gradual similarity for names using string algorithms
- score_pair: Weighted combination of multiple field comparisons
"""

from typing import Any, Literal

from rapidfuzz import fuzz

from .normalize import fsa, norm_email, norm_phone


def exact_match(a: str | None, b: str | None) -> bool:
    """Check if two strings are exactly equal.

    Used for deterministic fields like normalized email or phone where
    partial matches don't make sense.

    Args:
        a: First string
        b: Second string

    Returns:
        True if both non-None and equal, False otherwise

    Examples:
        >>> exact_match("test", "test")
        True
        >>> exact_match("test", "Test")  # Case sensitive!
        False
        >>> exact_match(None, "test")
        False
    """
    if not a or not b:
        return False
    return a == b


def fuzzy_score(
    a: str | None,
    b: str | None,
    method: Literal["jaro_winkler", "levenshtein", "ratio"] = "jaro_winkler",
) -> float:
    """Calculate fuzzy similarity between two strings.

    Uses rapidfuzz for high-performance string matching. Different methods
    are better for different use cases:

    - jaro_winkler: Best for names, handles typos and abbreviations well
      ("Jonathan" vs "Jon" = ~0.78)
    - levenshtein: Edit distance based, strict character-by-character
    - ratio: Simple ratio, good for general similarity

    Args:
        a: First string
        b: Second string
        method: Similarity algorithm to use

    Returns:
        Similarity score between 0.0 (completely different) and 1.0 (identical)

    Examples:
        >>> fuzzy_score("Jonathan", "Jon")
        0.78  # Good partial match
        >>> fuzzy_score("Smith", "Smyth")
        0.96  # Close spelling
        >>> fuzzy_score("Apple", "Orange")
        0.35  # Different words
    """
    if not a or not b:
        return 0.0

    if method == "jaro_winkler":
        # WRatio handles case and partial matching well
        return fuzz.WRatio(a, b) / 100.0
    elif method == "levenshtein":
        return fuzz.ratio(a, b) / 100.0
    else:  # ratio
        return fuzz.ratio(a, b) / 100.0


def score_pair(
    record_a: dict[str, Any],
    record_b: dict[str, Any],
    weights: dict[str, float],
) -> float:
    """Calculate weighted similarity score between two records.

    Combines multiple field comparisons using configurable weights.
    Each field comparison contributes to the total score based on its
    weight, allowing you to prioritize email matches over name matches.

    Default weight recommendations:
    - email_exact: 0.5 (email is highly reliable when present)
    - phone_exact: 0.3 (phone is reliable but may be shared)
    - name_fuzzy: 0.15 (names vary in spelling/nicknames)
    - postal_match: 0.05 (geographic confirmation)

    Args:
        record_a: First record as dict
        record_b: Second record as dict
        weights: Dict mapping comparison type to weight. Keys:
            - email_exact: Weight for email match
            - phone_exact: Weight for phone match
            - name_fuzzy: Weight for fuzzy name match
            - name_address: Weight for name + first initial match
            - postal_match: Weight for postal/FSA match

    Returns:
        Total score between 0.0 and 1.0 (capped)

    Examples:
        >>> a = {"email": "john@gmail.com", "phone": "5551234567", "last": "Doe"}
        >>> b = {"email": "john@gmail.com", "phone": "9999999999", "last": "Doe"}
        >>> weights = {"email_exact": 0.5, "phone_exact": 0.3, "name_address": 0.2}
        >>> score_pair(a, b, weights)
        0.7  # Email match (0.5) + name match (0.2)
    """
    score = 0.0

    # Email exact match (after normalization)
    if record_a.get("email") and record_b.get("email"):
        if norm_email(record_a["email"]) == norm_email(record_b["email"]):
            score += weights.get("email_exact", 0.5)

    # Phone exact match (after normalization)
    if record_a.get("phone") and record_b.get("phone"):
        if norm_phone(record_a["phone"]) == norm_phone(record_b["phone"]):
            score += weights.get("phone_exact", 0.3)

    # Fuzzy name match (if weight specified)
    if "name_fuzzy" in weights:
        name_a = f"{record_a.get('first', '')} {record_a.get('last', '')}".strip()
        name_b = f"{record_b.get('first', '')} {record_b.get('last', '')}".strip()
        if name_a and name_b:
            name_sim = fuzzy_score(name_a, name_b, method="jaro_winkler")
            score += weights["name_fuzzy"] * name_sim

    # Name + first initial match (simpler check)
    if "name_address" in weights:
        if record_a.get("last") and record_b.get("last"):
            last_match = record_a["last"].lower() == record_b["last"].lower()
            first_initial_a = (record_a.get("first") or "")[:1].lower()
            first_initial_b = (record_b.get("first") or "")[:1].lower()
            first_match = first_initial_a == first_initial_b

            if last_match and first_match:
                score += weights.get("name_address", 0.15)

    # Postal/FSA match
    if record_a.get("postal") and record_b.get("postal"):
        fsa_a = fsa(record_a.get("postal"))
        fsa_b = fsa(record_b.get("postal"))
        if fsa_a and fsa_a == fsa_b:
            score += weights.get("postal_match", 0.05)

    # Cap at 1.0
    return min(score, 1.0)
