"""
High-level identity resolution API.

The IdentityResolver class provides a simple interface for resolving duplicate
records into unified golden records.

Example:
    >>> from c1v_id import IdentityResolver
    >>> resolver = IdentityResolver()
    >>> records = [
    ...     {"email": "john@gmail.com", "phone": "555-1234", "name": "John Doe"},
    ...     {"email": "johnd@gmail.com", "phone": "555-1234", "name": "Johnny Doe"},
    ... ]
    >>> golden = resolver.resolve(records)
    >>> len(golden)  # One unified record
    1
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd

from c1v_id.blocking import generate_pairs, make_blocks
from c1v_id.clustering import UnionFind
from c1v_id.config import ResolverConfig
from c1v_id.golden import build_golden_records
from c1v_id.normalize import norm_address, norm_email, norm_name, norm_phone
from c1v_id.scoring import fuzzy_score


@dataclass
class MatchResult:
    """Result of matching two records.

    Attributes:
        score: Similarity score between 0.0 and 1.0
        decision: Classification based on thresholds ('auto_merge', 'needs_review', 'no_match')
        matched_on: List of fields that contributed to the match
        field_scores: Individual scores per field
    """

    score: float
    decision: str
    matched_on: list[str]
    field_scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "score": self.score,
            "decision": self.decision,
            "matched_on": self.matched_on,
            "field_scores": self.field_scores,
        }


class IdentityResolver:
    """Identity resolution engine.

    Resolves duplicate records into unified golden records using:
    - Blocking strategies for O(n) performance
    - Weighted multi-field scoring
    - Transitive clustering (if A≈B and B≈C, then A∈C)
    - Configurable survivorship rules

    Args:
        config: Optional ResolverConfig for customization. Uses sensible defaults if not provided.

    Example:
        >>> resolver = IdentityResolver()
        >>> records = [
        ...     {"email": "john@gmail.com", "name": "John Doe"},
        ...     {"email": "john@gmail.com", "name": "J. Doe"},
        ... ]
        >>> golden = resolver.resolve(records)

    With custom config:
        >>> from c1v_id import ResolverConfig, Thresholds
        >>> config = ResolverConfig(thresholds=Thresholds(auto_merge=0.95))
        >>> resolver = IdentityResolver(config=config)
    """

    def __init__(self, config: ResolverConfig | None = None) -> None:
        """Initialize resolver with optional configuration."""
        self.config = config or ResolverConfig()

    def match(self, record_a: dict[str, Any], record_b: dict[str, Any]) -> MatchResult:
        """Compare two records and return a match result.

        This is the core matching function. It normalizes both records,
        calculates per-field similarity scores, and returns an explainable result.

        Args:
            record_a: First record as a dictionary
            record_b: Second record as a dictionary

        Returns:
            MatchResult with score, decision, and explanation

        Example:
            >>> resolver = IdentityResolver()
            >>> result = resolver.match(
            ...     {"email": "john@gmail.com", "name": "John"},
            ...     {"email": "john@gmail.com", "name": "Johnny"}
            ... )
            >>> result.score
            0.95
            >>> result.decision
            'auto_merge'
            >>> result.matched_on
            ['email']
        """
        # Normalize both records
        a = self._normalize_record(record_a)
        b = self._normalize_record(record_b)

        # Calculate per-field scores
        field_scores: dict[str, float] = {}
        matched_on: list[str] = []

        weights = self.config.weights.normalized()

        # Email matching
        if a.get("email") and b.get("email"):
            if a["email"] == b["email"]:
                field_scores["email"] = 1.0
                matched_on.append("email")
            else:
                field_scores["email"] = fuzzy_score(a["email"], b["email"])
        else:
            field_scores["email"] = 0.0

        # Phone matching
        if a.get("phone") and b.get("phone"):
            if a["phone"] == b["phone"]:
                field_scores["phone"] = 1.0
                matched_on.append("phone")
            else:
                # Phones should match exactly or not at all
                field_scores["phone"] = 0.0
        else:
            field_scores["phone"] = 0.0

        # Name matching (fuzzy)
        name_a = self._get_full_name(a)
        name_b = self._get_full_name(b)
        if name_a and name_b:
            name_score = fuzzy_score(name_a, name_b)
            field_scores["name"] = name_score
            if name_score >= 0.85:
                matched_on.append("name")
        else:
            field_scores["name"] = 0.0

        # Address matching (fuzzy)
        if a.get("address") and b.get("address"):
            addr_score = fuzzy_score(a["address"], b["address"])
            field_scores["address"] = addr_score
            if addr_score >= 0.85:
                matched_on.append("address")
        else:
            field_scores["address"] = 0.0

        # Calculate weighted score (only count fields present in both records)
        # This prevents missing fields from dragging down the score
        active_fields = []
        if a.get("email") and b.get("email"):
            active_fields.append("email")
        if a.get("phone") and b.get("phone"):
            active_fields.append("phone")
        if name_a and name_b:
            active_fields.append("name")
        if a.get("address") and b.get("address"):
            active_fields.append("address")

        if not active_fields:
            total_score = 0.0
        else:
            # Renormalize weights for active fields only
            active_weight_sum = sum(weights[f] for f in active_fields)
            if active_weight_sum > 0:
                total_score = sum(
                    field_scores[f] * (weights[f] / active_weight_sum)
                    for f in active_fields
                )
            else:
                total_score = 0.0

        # Classify the result
        decision = self.config.thresholds.classify(total_score)

        return MatchResult(
            score=round(total_score, 4),
            decision=decision,
            matched_on=matched_on,
            field_scores={k: round(v, 4) for k, v in field_scores.items()},
        )

    def resolve(
        self,
        records: list[dict[str, Any]] | pd.DataFrame,
        id_field: str = "id",
    ) -> pd.DataFrame:
        """Resolve a list of records into deduplicated golden records.

        This is the main entry point for batch resolution. It:
        1. Normalizes all records
        2. Applies blocking strategies to find candidate pairs
        3. Scores each candidate pair
        4. Clusters matches transitively
        5. Builds golden records from each cluster

        Args:
            records: List of record dicts or a pandas DataFrame
            id_field: Name of the unique identifier field (default: 'id')

        Returns:
            DataFrame with golden records, each containing:
            - All survived field values
            - cluster_id: Unique identifier for the cluster
            - source_count: Number of records merged
            - sources: List of source systems represented
            - source_ids: List of original record IDs

        Example:
            >>> resolver = IdentityResolver()
            >>> records = [
            ...     {"id": "r1", "email": "john@gmail.com", "name": "John Doe"},
            ...     {"id": "r2", "email": "john@gmail.com", "name": "J Doe"},
            ...     {"id": "r3", "email": "jane@gmail.com", "name": "Jane Doe"},
            ... ]
            >>> golden = resolver.resolve(records)
            >>> len(golden)  # r1 and r2 merged, r3 separate
            2
        """
        # Convert to DataFrame if needed
        if isinstance(records, list):
            df = pd.DataFrame(records)
        else:
            df = records.copy()

        # Ensure we have an ID field
        if id_field not in df.columns:
            df[id_field] = range(len(df))

        # Normalize all records
        df = self._normalize_dataframe(df)

        # Apply blocking to get candidate pairs
        # make_blocks returns columns block_0, block_1, etc.
        # We generate pairs from each blocking column and deduplicate
        try:
            block_df = make_blocks(df, self.config.blocking_strategies)
        except (KeyError, ValueError):
            # If blocking fails (missing columns), skip blocking
            block_df = None

        pairs: set[tuple[int, int]] = set()
        if block_df is not None:
            for col in block_df.columns:
                # Combine block column with original index
                temp_df = df.copy()
                temp_df["_block"] = block_df[col]
                col_pairs = generate_pairs(temp_df, "_block")
                pairs.update(col_pairs)

        pairs_list = list(pairs)

        if not pairs_list:
            # No blocking matches — each record is its own cluster
            clusters = {i: [i] for i in df.index}
            return build_golden_records(
                df,
                clusters,
                self.config.survivorship_rules,
                self.config.source_priority,
            )

        # Score each pair and find matches
        uf = UnionFind(list(df.index))
        threshold = self.config.thresholds.auto_merge

        for idx_a, idx_b in pairs_list:
            record_a = df.loc[idx_a].to_dict()
            record_b = df.loc[idx_b].to_dict()
            result = self.match(record_a, record_b)

            if result.score >= threshold:
                uf.union(idx_a, idx_b)

        # Get clusters
        clusters = uf.get_clusters()

        # Build golden records
        golden = build_golden_records(
            df,
            clusters,
            self.config.survivorship_rules,
            self.config.source_priority,
        )

        return golden

    def find_matches(
        self,
        record: dict[str, Any],
        candidates: list[dict[str, Any]] | pd.DataFrame,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Find all matching records for a given record.

        Useful for checking if an incoming record matches any existing records.

        Args:
            record: The record to match against candidates
            candidates: List of candidate records or DataFrame
            threshold: Minimum score to consider a match (default: needs_review threshold)

        Returns:
            List of matches, each containing the candidate record and match result

        Example:
            >>> resolver = IdentityResolver()
            >>> incoming = {"email": "john@gmail.com", "name": "John"}
            >>> existing = [
            ...     {"id": "1", "email": "john@gmail.com", "name": "John Doe"},
            ...     {"id": "2", "email": "jane@gmail.com", "name": "Jane Doe"},
            ... ]
            >>> matches = resolver.find_matches(incoming, existing)
            >>> len(matches)
            1
        """
        if threshold is None:
            threshold = self.config.thresholds.needs_review

        if isinstance(candidates, pd.DataFrame):
            candidates = candidates.to_dict("records")

        matches = []
        for candidate in candidates:
            result = self.match(record, candidate)
            if result.score >= threshold:
                matches.append({
                    "record": candidate,
                    "match": result.to_dict(),
                })

        # Sort by score descending
        matches.sort(key=lambda x: x["match"]["score"], reverse=True)
        return matches

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single record's fields."""
        result = record.copy()

        if "email" in result and result["email"]:
            result["email"] = norm_email(str(result["email"]))

        if "phone" in result and result["phone"]:
            result["phone"] = norm_phone(str(result["phone"]))

        # Handle name (could be single field or first/last)
        if "name" in result and result["name"]:
            result["name"] = norm_name(str(result["name"]))
        if "first" in result and result["first"]:
            result["first"] = norm_name(str(result["first"]))
        if "last" in result and result["last"]:
            result["last"] = norm_name(str(result["last"]))

        if "address" in result and result["address"]:
            result["address"] = norm_address(str(result["address"]))

        return result

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize all fields in a DataFrame."""
        result = df.copy()

        if "email" in result.columns:
            result["email"] = result["email"].apply(
                lambda x: norm_email(str(x)) if pd.notna(x) else None
            )

        if "phone" in result.columns:
            result["phone"] = result["phone"].apply(
                lambda x: norm_phone(str(x)) if pd.notna(x) else None
            )

        if "name" in result.columns:
            result["name"] = result["name"].apply(
                lambda x: norm_name(str(x)) if pd.notna(x) else None
            )

        if "first" in result.columns:
            result["first"] = result["first"].apply(
                lambda x: norm_name(str(x)) if pd.notna(x) else None
            )

        if "last" in result.columns:
            result["last"] = result["last"].apply(
                lambda x: norm_name(str(x)) if pd.notna(x) else None
            )

        if "address" in result.columns:
            result["address"] = result["address"].apply(
                lambda x: norm_address(str(x)) if pd.notna(x) else None
            )

        return result

    def _get_full_name(self, record: dict[str, Any]) -> str | None:
        """Extract full name from record (handles both 'name' and 'first'/'last')."""
        if record.get("name"):
            return record["name"]
        elif record.get("first") or record.get("last"):
            parts = [record.get("first", ""), record.get("last", "")]
            return " ".join(p for p in parts if p).strip() or None
        return None
