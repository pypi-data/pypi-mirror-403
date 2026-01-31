"""Input validation utilities for Pincho library."""

import re
from typing import List, Optional


def normalize_tags(tags: Optional[List[str]]) -> List[str]:
    """Normalize tags: lowercase, trim, strip invalid chars, remove duplicates.

    Args:
        tags: Optional list of tags to normalize

    Returns:
        Normalized list of tags (empty list if no valid tags)

    Example:
        >>> normalize_tags(['Production', '  Release  ', 'production', 'Deploy'])
        ['production', 'release', 'deploy']
        >>> normalize_tags(['special@chars!', 'valid-tag'])
        ['specialchars', 'valid-tag']
    """
    if tags is None or not tags:
        return []

    # Normalize: lowercase, trim whitespace, strip invalid chars, remove duplicates
    normalized = []
    seen: set[str] = set()

    for tag in tags:
        if not isinstance(tag, str):
            continue

        # Lowercase and trim
        cleaned = tag.lower().strip()

        # Strip invalid characters (keep only alphanumeric, hyphens, underscores)
        cleaned = re.sub(r"[^a-z0-9_-]", "", cleaned)

        # Skip empty tags
        if not cleaned:
            continue

        # Skip duplicates (case-insensitive)
        if cleaned in seen:
            continue

        normalized.append(cleaned)
        seen.add(cleaned)

    return normalized
