"""
c1v-id: Identity resolution for AI applications.

Resolve duplicate records into unified golden records in 10 lines of Python.

Quick example:
    >>> from c1v_id import IdentityResolver
    >>> resolver = IdentityResolver()
    >>> records = [
    ...     {"email": "john@gmail.com", "name": "John Doe"},
    ...     {"email": "john@gmail.com", "name": "J. Doe"},
    ... ]
    >>> golden = resolver.resolve(records)
    >>> len(golden)
    1

Match two records:
    >>> result = resolver.match(
    ...     {"email": "john@gmail.com", "name": "John"},
    ...     {"email": "john@gmail.com", "name": "Johnny"}
    ... )
    >>> result.score, result.decision
    (0.95, 'auto_merge')

Low-level functions are also available for custom pipelines.
"""

__version__ = "0.1.0"

# High-level API (recommended)
# Blocking strategies
from c1v_id.blocking import (
    email_domain_last4,
    email_exact,
    generate_pairs,
    make_blocks,
    name_fsa,
    phone_last7,
)

# Clustering
from c1v_id.clustering import (
    UnionFind,
    cluster_records,
)
from c1v_id.config import ResolverConfig, Thresholds, Weights

# Golden records
from c1v_id.golden import (
    DEFAULT_SURVIVORSHIP_RULES,
    SurvivorshipRule,
    build_golden_records,
    survivorship,
)

# Normalization functions
from c1v_id.normalize import (
    fsa,
    norm_address,
    norm_email,
    norm_name,
    norm_phone,
)
from c1v_id.resolver import IdentityResolver, MatchResult

# Scoring functions
from c1v_id.scoring import (
    exact_match,
    fuzzy_score,
    score_pair,
)

__all__ = [
    # Version
    "__version__",
    # High-level API
    "IdentityResolver",
    "MatchResult",
    "ResolverConfig",
    "Thresholds",
    "Weights",
    # Normalization
    "norm_email",
    "norm_phone",
    "norm_name",
    "norm_address",
    "fsa",
    # Blocking
    "email_domain_last4",
    "phone_last7",
    "name_fsa",
    "email_exact",
    "make_blocks",
    "generate_pairs",
    # Scoring
    "exact_match",
    "fuzzy_score",
    "score_pair",
    # Clustering
    "UnionFind",
    "cluster_records",
    # Golden records
    "SurvivorshipRule",
    "survivorship",
    "build_golden_records",
    "DEFAULT_SURVIVORSHIP_RULES",
]
