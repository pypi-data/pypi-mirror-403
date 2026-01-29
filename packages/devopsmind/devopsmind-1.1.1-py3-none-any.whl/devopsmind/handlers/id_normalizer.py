"""
Lab ID normalization utilities.

Design guarantees:
- Backward compatible with legacy snake_case IDs
- Canonical internal representation uses kebab-case
- No hardcoded mappings
- Mechanical, deterministic, offline-safe
"""

def canonical_id(cid: str) -> str:
    """
    Normalize a lab ID to its canonical form.

    Rules:
    - kebab-case is canonical
    - snake_case is legacy
    - normalization is mechanical (underscore → hyphen)
    - unknown formats pass through unchanged
    """
    if not isinstance(cid, str):
        return cid

    return cid.replace("_", "-")
