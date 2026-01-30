"""Cache key generation utilities."""

import hashlib
import json


def normalize_filters(filters: list[dict] | None) -> list[dict]:
    """
    Normalize filters for consistent cache keys.

    Converts filter dicts to a canonical form and sorts them
    to ensure order-independent key generation.

    Args:
        filters: List of filter dicts with dimension, operator, value keys

    Returns:
        Sorted list of normalized filter dicts
    """
    if not filters:
        return []

    normalized = []
    for f in filters:
        normalized.append({
            "d": f["dimension"],
            "o": f["operator"],
            "v": f["value"],
        })

    # Sort by dimension, then operator, then value (as string)
    return sorted(normalized, key=lambda x: (x["d"], x["o"], str(x["v"])))


def query_cache_key(
    org_id: str,
    metrics: list[str],
    dimensions: list[str] | None,
    grain: str | None,
    start_date: str | None,
    end_date: str | None,
    filters: list[dict] | None,
    comparison: str | None,
    order_by: str | None,
    limit: int | None,
) -> str:
    """
    Generate a deterministic cache key for a query.

    The key is built from a normalized representation of all query
    parameters, ensuring that equivalent queries produce the same key
    regardless of parameter order.

    Args:
        org_id: Organization ID
        metrics: List of metric names
        dimensions: List of dimension names (optional)
        grain: Time grain (day, week, month, etc.)
        start_date: Start date in ISO format
        end_date: End date in ISO format
        filters: List of filter dicts
        comparison: Comparison type (previous_period, etc.)
        order_by: Order by clause
        limit: Result limit

    Returns:
        Cache key in format "org_id:hash"
    """
    # Normalize all inputs for consistent hashing
    normalized = {
        "m": sorted(metrics),
        "d": sorted(dimensions) if dimensions else None,
        "g": grain,
        "s": start_date,
        "e": end_date,
        "f": normalize_filters(filters),
        "c": comparison,
        "o": order_by,
        "l": limit,
    }

    # Create deterministic JSON (sorted keys, minimal separators)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))

    # Hash to fixed-length key
    hash_digest = hashlib.sha256(payload.encode()).hexdigest()[:12]

    return f"{org_id}:{hash_digest}"
