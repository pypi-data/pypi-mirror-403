"""Manifest utilities for cache freshness.

This module is intentionally lightweight (no heavy dependencies)
so it can be imported by tests without google.cloud dependencies.
"""


def extract_datasets_from_manifest(manifest: dict) -> list[str]:
    """Extract unique dataset names from semantic manifest.

    Each semantic model has a node_relation with schema_name which
    corresponds to the BigQuery dataset. Metrics can span multiple
    semantic models, so we collect all unique datasets.

    Args:
        manifest: Semantic manifest dict

    Returns:
        List of unique dataset names (BigQuery datasets / schema names)
    """
    datasets = set()
    for model in manifest.get("semantic_models", []):
        node_relation = model.get("node_relation", {})
        schema_name = node_relation.get("schema_name")
        if schema_name:
            datasets.add(schema_name)
    return sorted(datasets)  # Sorted for consistent ordering
