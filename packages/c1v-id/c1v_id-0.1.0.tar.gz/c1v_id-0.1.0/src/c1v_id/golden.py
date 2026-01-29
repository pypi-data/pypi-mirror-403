"""
Golden record creation with configurable survivorship rules.

A "golden record" is the single best representation of an entity created
by merging multiple duplicate records. Survivorship rules determine which
value wins when records have conflicting data.

Example: Two records for the same person
- Record A: email=john@old.com (from 2023), phone=None
- Record B: email=john@new.com (from 2024), phone=555-1234

With MOST_RECENT for email, the golden record gets john@new.com.
With FIRST_NON_NULL for phone, the golden record gets 555-1234.
"""

from enum import Enum
from typing import Any

import pandas as pd


class SurvivorshipRule(str, Enum):
    """Survivorship rule types for golden record field selection.

    These rules determine which value "survives" when merging multiple
    records with potentially conflicting data.

    Attributes:
        MOST_RECENT: Use value from most recently updated record
        LONGEST: Use the longest non-null value (good for addresses)
        SOURCE_PRIORITY: Use value from highest-priority source
        FIRST_NON_NULL: Use first non-null value encountered
    """

    MOST_RECENT = "most_recent"
    LONGEST = "longest"
    SOURCE_PRIORITY = "source_priority"
    FIRST_NON_NULL = "first_non_null"


# Default rules that work well for most identity resolution use cases
DEFAULT_SURVIVORSHIP_RULES: dict[str, SurvivorshipRule] = {
    "email": SurvivorshipRule.MOST_RECENT,
    "phone": SurvivorshipRule.MOST_RECENT,
    "first": SurvivorshipRule.FIRST_NON_NULL,
    "last": SurvivorshipRule.FIRST_NON_NULL,
    "address": SurvivorshipRule.LONGEST,
    "postal": SurvivorshipRule.FIRST_NON_NULL,
    "city": SurvivorshipRule.FIRST_NON_NULL,
}


def survivorship(
    group: pd.DataFrame,
    rules: dict[str, str | SurvivorshipRule],
    source_priority: list[str],
) -> dict[str, Any]:
    """Apply survivorship rules to create a golden record from a cluster.

    Takes a group of duplicate records and picks the best value for each
    field based on the configured rules.

    Args:
        group: DataFrame containing all records in a cluster
        rules: Dict mapping field name → survivorship rule
        source_priority: Ordered list of source names (highest priority first)

    Returns:
        Dict containing the golden record with best values for each field,
        plus metadata (source_ids, source_count, sources)

    Examples:
        >>> cluster = pd.DataFrame({
        ...     "id": ["r1", "r2"],
        ...     "source": ["crm", "web"],
        ...     "email": ["john@old.com", "john@new.com"],
        ...     "updated_at": ["2023-01-01", "2024-01-01"]
        ... })
        >>> rules = {"email": SurvivorshipRule.MOST_RECENT}
        >>> golden = survivorship(cluster, rules, ["crm", "web"])
        >>> golden["email"]
        'john@new.com'
    """
    result: dict[str, Any] = {}

    # Sort by source priority and recency
    g = group.copy()

    if source_priority and "source" in g.columns:
        # Create priority index (lower = higher priority)
        g["_priority"] = g["source"].apply(
            lambda s: source_priority.index(s) if s in source_priority else len(source_priority)
        )
        sort_cols = ["_priority"]
        if "updated_at" in g.columns:
            sort_cols.append("updated_at")
        g = g.sort_values(sort_cols, ascending=[True, False], na_position="last")
    elif "updated_at" in g.columns:
        g = g.sort_values("updated_at", ascending=False, na_position="last")

    # Apply survivorship rules for each field
    standard_fields = ["email", "phone", "first", "last", "address", "postal", "city", "region"]

    for field in standard_fields:
        if field not in g.columns:
            continue

        # Get rule for this field (default to FIRST_NON_NULL)
        rule = rules.get(field, SurvivorshipRule.FIRST_NON_NULL)
        if isinstance(rule, str):
            rule = SurvivorshipRule(rule)

        # Get non-null candidates
        non_null = g[g[field].notna()]

        if non_null.empty:
            result[field] = None
            continue

        if rule == SurvivorshipRule.MOST_RECENT:
            # Already sorted by recency, take first non-null
            result[field] = non_null.iloc[0][field]

        elif rule == SurvivorshipRule.LONGEST:
            # Pick longest string value
            candidates = non_null[field]
            result[field] = max(candidates, key=lambda x: len(str(x)) if x else 0)

        elif rule == SurvivorshipRule.SOURCE_PRIORITY:
            # Already sorted by priority, take first non-null
            result[field] = non_null.iloc[0][field]

        else:  # FIRST_NON_NULL
            result[field] = non_null.iloc[0][field]

    # Collect source metadata
    if "source" in g.columns and "id" in g.columns:
        result["source_ids"] = list(zip(g["source"], g["id"]))
    elif "id" in g.columns:
        result["source_ids"] = list(g["id"])
    else:
        result["source_ids"] = list(g.index)

    result["source_count"] = len(g)

    if "source" in g.columns:
        result["sources"] = sorted(g["source"].dropna().unique().tolist())
    else:
        result["sources"] = []

    return result


def build_golden_records(
    df: pd.DataFrame,
    clusters: dict[int, list[int]],
    rules: dict[str, str | SurvivorshipRule] | None = None,
    source_priority: list[str] | None = None,
) -> pd.DataFrame:
    """Build golden records for all clusters.

    Takes the original records and cluster assignments, then creates
    one golden record per cluster by applying survivorship rules.

    Args:
        df: Original DataFrame with all records
        clusters: Dict mapping cluster_id → list of record indices
        rules: Survivorship rules per field (uses defaults if None)
        source_priority: Ordered source names (highest priority first)

    Returns:
        DataFrame with one golden record per cluster, including:
        - All survived field values
        - cluster_id: The cluster identifier
        - source_count: Number of records merged
        - sources: List of source systems represented
        - source_ids: List of (source, id) tuples for traceability

    Examples:
        >>> df = pd.DataFrame({
        ...     "id": ["r1", "r2", "r3"],
        ...     "email": ["a@x.com", "a@x.com", "b@y.com"],
        ...     "source": ["crm", "web", "crm"]
        ... })
        >>> clusters = {0: [0, 1], 2: [2]}  # r1+r2 merged, r3 alone
        >>> golden = build_golden_records(df, clusters)
        >>> len(golden)
        2
    """
    if rules is None:
        rules = DEFAULT_SURVIVORSHIP_RULES

    if source_priority is None:
        source_priority = []

    golden_records = []

    for cluster_id, member_indices in clusters.items():
        # Get all records in this cluster
        cluster_df = df.loc[member_indices]

        # Apply survivorship to get golden record
        golden = survivorship(cluster_df, rules, source_priority)
        golden["cluster_id"] = cluster_id

        golden_records.append(golden)

    return pd.DataFrame(golden_records)
