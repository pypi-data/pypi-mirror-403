"""
Data normalization functions for identity resolution.

These functions clean and standardize input data to enable accurate matching.
Normalization is critical because the same person might appear as:
- "John.Doe+newsletter@Gmail.com" vs "johndoe@gmail.com"
- "(555) 123-4567" vs "1-555-123-4567"
- "  JOHN   DOE  " vs "john doe"
"""

import re


def norm_email(email: str | None) -> str | None:
    """Normalize an email address for matching.

    Transformations applied:
    1. Lowercase the entire email
    2. Strip leading/trailing whitespace
    3. Remove +tags (e.g., john+spam@gmail.com → john@gmail.com)
    4. For Gmail: remove dots from local part (j.o.h.n → john)

    Args:
        email: Raw email string, or None

    Returns:
        Normalized email, or None if invalid/empty

    Examples:
        >>> norm_email("John.Doe+tag@Gmail.com")
        'johndoe@gmail.com'
        >>> norm_email("  test@example.com  ")
        'test@example.com'
        >>> norm_email(None)
        None
    """
    if not email or not isinstance(email, str):
        return None

    email = email.strip().lower()
    if "@" not in email:
        return None

    local, _, domain = email.partition("@")

    # Remove everything after + (gmail-style tags)
    local = re.sub(r"\+.*$", "", local)

    # Remove dots from local part for Gmail addresses
    if domain in ["gmail.com", "googlemail.com"]:
        local = local.replace(".", "")

    return f"{local}@{domain}"


def norm_phone(phone: str | None) -> str | None:
    """Normalize a phone number to digits only.

    Transformations applied:
    1. Extract digits only (remove parentheses, dashes, spaces)
    2. Remove leading country code "1" if 11 digits
    3. Require minimum 7 digits

    Args:
        phone: Raw phone string, or None

    Returns:
        Normalized phone (digits only), or None if invalid/too short

    Examples:
        >>> norm_phone("(555) 123-4567")
        '5551234567'
        >>> norm_phone("1-555-123-4567")
        '5551234567'
        >>> norm_phone("123")  # Too short
        None
    """
    if not phone or not isinstance(phone, str):
        return None

    # Extract digits only
    digits = re.sub(r"\D", "", phone)

    # Must have at least 7 digits
    if len(digits) < 7:
        return None

    # Remove country code 1 if present (11 digits starting with 1)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    return digits


def norm_name(name: str | None) -> str | None:
    """Normalize a name for matching.

    Transformations applied:
    1. Strip leading/trailing whitespace
    2. Lowercase
    3. Collapse multiple spaces to single space

    Args:
        name: Raw name string, or None

    Returns:
        Normalized name, or None if empty

    Examples:
        >>> norm_name("  John   Doe  ")
        'john doe'
        >>> norm_name("JANE")
        'jane'
        >>> norm_name(None)
        None
    """
    if not name or not isinstance(name, str):
        return None

    return re.sub(r"\s+", " ", name.strip().lower())


def norm_address(address: str | None) -> str | None:
    """Normalize a street address.

    Transformations applied:
    1. Strip whitespace and lowercase
    2. Collapse multiple spaces
    3. Standardize abbreviations (st→street, ave→avenue, etc.)

    Args:
        address: Raw address string, or None

    Returns:
        Normalized address, or None if empty

    Examples:
        >>> norm_address("123 Main St.")
        '123 main street'
        >>> norm_address("456 Park Ave")
        '456 park avenue'
    """
    if not address or not isinstance(address, str):
        return None

    # Basic cleanup
    addr = address.strip().lower()

    # Remove extra spaces
    addr = re.sub(r"\s+", " ", addr)

    # Standardize common abbreviations
    replacements = {
        " st ": " street ",
        " st.": " street",
        " ave ": " avenue ",
        " ave.": " avenue",
        " rd ": " road ",
        " rd.": " road",
        " dr ": " drive ",
        " dr.": " drive",
        " ln ": " lane ",
        " ln.": " lane",
        " blvd ": " boulevard ",
        " blvd.": " boulevard",
    }

    for old, new in replacements.items():
        addr = addr.replace(old, new)

    return addr


def fsa(postal: str | None) -> str | None:
    """Extract Forward Sortation Area (first 3 characters of postal code).

    Works for Canadian postal codes (e.g., "M5V 3A8" → "M5V") and
    US ZIP codes (e.g., "90210" → "902").

    Args:
        postal: Raw postal/ZIP code, or None

    Returns:
        First 3 alphanumeric characters, uppercase, or None if too short

    Examples:
        >>> fsa("M5V 3A8")
        'M5V'
        >>> fsa("90210")
        '902'
        >>> fsa("AB")  # Too short
        None
    """
    if not postal or not isinstance(postal, str):
        return None

    # Remove all non-alphanumeric characters
    clean = re.sub(r"\W+", "", postal).upper()

    # Return first 3 characters if available
    return clean[:3] if len(clean) >= 3 else None
