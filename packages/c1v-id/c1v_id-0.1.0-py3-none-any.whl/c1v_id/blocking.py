"""
Blocking strategies for identity resolution.

Blocking reduces comparison complexity from O(n²) to approximately O(n) by
grouping records that are likely to match. Only records in the same "block"
are compared, dramatically reducing the number of comparisons needed.

Example: 10,000 records
- Without blocking: 50 million comparisons (n choose 2)
- With blocking: ~10,000 comparisons (records only compared within blocks)

Blocking keys are intentionally loose to avoid false negatives. It's better
to compare a few extra pairs than to miss a match.
"""

import itertools
from typing import Literal

import pandas as pd

from .normalize import fsa, norm_email, norm_phone

# Type alias for blocking strategy names
BlockingStrategy = Literal["email_domain_last4", "phone_last7", "name_fsa", "email_exact"]


def email_domain_last4(email: str | None) -> str | None:
    """Create blocking key from email domain + last 4 chars of local part.

    This groups emails that share the same domain and have similar local parts.
    Catches variations like john.doe@gmail.com and johndoe@gmail.com.

    Args:
        email: Raw email address

    Returns:
        Blocking key like "gmail.com|ndoe", or None if invalid

    Examples:
        >>> email_domain_last4("john.doe@gmail.com")
        'gmail.com|ndoe'
        >>> email_domain_last4("jd@example.com")
        'example.com|jd'
    """
    if not email:
        return None

    e = norm_email(email)
    if not e:
        return None

    local, _, domain = e.partition("@")

    # Get last 4 alphanumeric characters (or all if shorter)
    if len(local) >= 4:
        return f"{domain}|{local[-4:]}"
    else:
        return f"{domain}|{local}"


def phone_last7(phone: str | None) -> str | None:
    """Create blocking key from last 7 digits of phone number.

    Ignores area code variations and country codes, catching:
    - (555) 123-4567 and 555-123-4567
    - 1-555-123-4567 and +1 555 123 4567

    Args:
        phone: Raw phone number

    Returns:
        Last 7 digits, or None if invalid/too short

    Examples:
        >>> phone_last7("(555) 123-4567")
        '1234567'
        >>> phone_last7("1-800-555-1234")
        '5551234'
    """
    p = norm_phone(phone)
    return p[-7:] if p and len(p) >= 7 else None


def name_fsa(first: str | None, last: str | None, postal: str | None) -> str | None:
    """Create blocking key from last name + first initial + postal FSA.

    Groups people with the same last name and first initial in the same
    geographic area. Catches name variations like "John" vs "Johnny".

    Args:
        first: First name
        last: Last name (required)
        postal: Postal/ZIP code

    Returns:
        Blocking key like "doe|j|M5V", or None if no last name

    Examples:
        >>> name_fsa("John", "Doe", "M5V 3A8")
        'doe|j|M5V'
        >>> name_fsa("Johnny", "Doe", "M5V 1A1")
        'doe|j|M5V'
    """
    if not last:
        return None

    last_clean = (last or "").strip().lower()
    first_initial = (first or "").strip()[:1].lower()
    postal_fsa = fsa(postal) or ""

    return f"{last_clean}|{first_initial}|{postal_fsa}"


def email_exact(email: str | None) -> str | None:
    """Create blocking key from exact normalized email.

    The most precise blocking strategy - only exact email matches
    are compared. Use when email is highly reliable.

    Args:
        email: Raw email address

    Returns:
        Normalized email, or None if invalid

    Examples:
        >>> email_exact("John.Doe@Gmail.com")
        'johndoe@gmail.com'
    """
    return norm_email(email)


def make_blocks(df: pd.DataFrame, strategies: list[str]) -> pd.DataFrame:
    """Apply multiple blocking strategies to a DataFrame.

    Creates blocking keys for each record using the specified strategies.
    Records with matching blocking keys will be compared.

    Args:
        df: DataFrame with records to block. Expected columns depend on
            strategies used (email, phone, first, last, postal).
        strategies: List of strategy names to apply. Options:
            - "email_domain_last4": Groups by domain + last 4 chars
            - "phone_last7": Groups by last 7 digits
            - "name_fsa": Groups by last name + first initial + postal area
            - "email_exact": Groups by exact normalized email

    Returns:
        DataFrame with blocking key columns (block_0, block_1, etc.)

    Examples:
        >>> df = pd.DataFrame({"email": ["john@gmail.com"], "phone": ["555-1234"]})
        >>> blocks = make_blocks(df, ["email_domain_last4", "phone_last7"])
        >>> blocks.columns.tolist()
        ['block_0', 'block_1']
    """
    blocks = []

    for strategy in strategies:
        if strategy == "email_domain_last4":
            if "email" in df.columns:
                blocks.append(df["email"].apply(email_domain_last4))
        elif strategy == "phone_last7":
            if "phone" in df.columns:
                blocks.append(df["phone"].apply(phone_last7))
        elif strategy == "name_fsa":
            # name_fsa needs first, last, and postal
            if "first" in df.columns or "last" in df.columns:
                blocks.append(
                    df.apply(
                        lambda r: name_fsa(r.get("first"), r.get("last"), r.get("postal")),
                        axis=1,
                    )
                )
        elif strategy == "email_exact":
            if "email" in df.columns:
                blocks.append(df["email"].apply(email_exact))
        else:
            raise ValueError(f"Unknown blocking strategy: {strategy}")

    # Combine all blocking keys into a DataFrame
    block_df = pd.concat(blocks, axis=1)
    block_df.columns = [f"block_{i}" for i in range(len(blocks))]

    return block_df.fillna("")


def generate_pairs(
    df: pd.DataFrame, block_col: str = "block_key"
) -> list[tuple[int, int]]:
    """Generate candidate pairs from records sharing the same block key.

    Only pairs within the same block are returned, dramatically reducing
    the total number of comparisons needed.

    Args:
        df: DataFrame with a blocking key column
        block_col: Name of the column containing the composite block key

    Returns:
        List of (index_a, index_b) tuples for records to compare

    Examples:
        >>> df = pd.DataFrame({"block_key": ["A", "A", "B"]})
        >>> generate_pairs(df, "block_key")
        [(0, 1)]  # Only indices 0 and 1 share block "A"
    """
    pairs = []

    for block_val, group in df.groupby(block_col):
        # Skip empty blocks
        if not block_val or block_val == "":
            continue

        ids = list(group.index)

        # Generate all pairs within this block
        for i, j in itertools.combinations(ids, 2):
            pairs.append((i, j))

    return pairs
