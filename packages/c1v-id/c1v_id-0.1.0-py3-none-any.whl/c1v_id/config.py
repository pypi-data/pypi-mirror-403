"""
Configuration for identity resolution.

Provides dataclasses for configuring thresholds, weights, and blocking strategies.
All values have sensible defaults — you can use IdentityResolver() with no config.

Example:
    >>> from c1v_id import ResolverConfig
    >>> config = ResolverConfig(auto_merge_threshold=0.95)  # Stricter matching
    >>> resolver = IdentityResolver(config=config)
"""

from dataclasses import dataclass, field
from typing import Literal

from c1v_id.golden import SurvivorshipRule


@dataclass
class Thresholds:
    """Decision thresholds for match classification.

    Attributes:
        auto_merge: Score >= this means records are the same entity (default: 0.9)
        needs_review: Score >= this but < auto_merge means possible match (default: 0.7)
        no_match: Score < needs_review means different entities

    Example:
        >>> t = Thresholds(auto_merge=0.95, needs_review=0.8)
        >>> t.classify(0.92)
        'needs_review'
        >>> t.classify(0.96)
        'auto_merge'
    """

    auto_merge: float = 0.9
    needs_review: float = 0.7

    def classify(self, score: float) -> Literal["auto_merge", "needs_review", "no_match"]:
        """Classify a similarity score into a decision."""
        if score >= self.auto_merge:
            return "auto_merge"
        elif score >= self.needs_review:
            return "needs_review"
        else:
            return "no_match"


@dataclass
class Weights:
    """Attribute weights for similarity scoring.

    Higher weight = more influence on final score.
    Weights are normalized internally, so relative values matter.

    Attributes:
        email: Weight for email matching (default: 0.5) — highest because emails are unique
        phone: Weight for phone matching (default: 0.3) — phones can be shared
        name: Weight for name matching (default: 0.15) — names are often similar
        address: Weight for address matching (default: 0.05) — addresses change

    Example:
        >>> w = Weights(email=0.6, phone=0.4, name=0.0)  # Ignore name
    """

    email: float = 0.5
    phone: float = 0.3
    name: float = 0.15
    address: float = 0.05

    def to_dict(self) -> dict[str, float]:
        """Convert to dict for score_pair function."""
        return {
            "email": self.email,
            "phone": self.phone,
            "name": self.name,
            "address": self.address,
        }

    def normalized(self) -> dict[str, float]:
        """Return weights normalized to sum to 1.0."""
        total = self.email + self.phone + self.name + self.address
        if total == 0:
            return {"email": 0.25, "phone": 0.25, "name": 0.25, "address": 0.25}
        return {
            "email": self.email / total,
            "phone": self.phone / total,
            "name": self.name / total,
            "address": self.address / total,
        }


@dataclass
class ResolverConfig:
    """Complete configuration for IdentityResolver.

    All fields have sensible defaults — create with ResolverConfig() for standard behavior.

    Attributes:
        thresholds: Decision thresholds for auto_merge/needs_review/no_match
        weights: Attribute weights for similarity scoring
        blocking_strategies: Which blocking strategies to use (default: all)
        survivorship_rules: How to pick winning values for golden records
        source_priority: Ordered list of source names (highest priority first)

    Example:
        >>> config = ResolverConfig(
        ...     thresholds=Thresholds(auto_merge=0.95),
        ...     weights=Weights(email=0.6, phone=0.4),
        ... )
    """

    thresholds: Thresholds = field(default_factory=Thresholds)
    weights: Weights = field(default_factory=Weights)
    blocking_strategies: list[str] = field(
        default_factory=lambda: ["email_domain_last4", "phone_last7", "name_fsa"]
    )
    survivorship_rules: dict[str, SurvivorshipRule] = field(default_factory=dict)
    source_priority: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Apply defaults for survivorship rules if not provided."""
        if not self.survivorship_rules:
            self.survivorship_rules = {
                "email": SurvivorshipRule.MOST_RECENT,
                "phone": SurvivorshipRule.MOST_RECENT,
                "first": SurvivorshipRule.FIRST_NON_NULL,
                "last": SurvivorshipRule.FIRST_NON_NULL,
                "address": SurvivorshipRule.LONGEST,
            }
