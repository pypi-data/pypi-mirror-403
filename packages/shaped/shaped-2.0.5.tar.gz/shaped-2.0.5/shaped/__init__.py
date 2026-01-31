"""
Shaped Python SDK public API.

This module re-exports the primary user-facing symbols so users can write:

    from shaped import Client, Engine, Table, View
    from shaped import RankQueryBuilder, Similarity, ColumnOrder

Keep this file lightweight and stable: it is part of the SDK's public surface.
"""

from __future__ import annotations

from shaped.client import Client, ViewConfig
from shaped.config_builders import Engine, Table, View
from shaped.query_builder import (
    Boosted,
    CandidateAttributes,
    CandidateIds,
    ColumnOrder,
    Diversity,
    Exploration,
    Expression,
    Filter,
    Passthrough,
    Prebuilt,
    RankQueryBuilder,
    Similarity,
    TextSearch,
    Truncate,
    ensemble,
)

# Backwards-compatible alias.
Ensemble = ensemble

__all__ = [
    "Boosted",
    "CandidateAttributes",
    "CandidateIds",
    "Client",
    "ColumnOrder",
    "Diversity",
    "Ensemble",
    "Engine",
    "Exploration",
    "Expression",
    "Filter",
    "Passthrough",
    "Prebuilt",
    "RankQueryBuilder",
    "Similarity",
    "Table",
    "TextSearch",
    "Truncate",
    "View",
    "ViewConfig",
    "ensemble",
]
