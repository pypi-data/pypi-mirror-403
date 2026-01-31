"""
Token cost estimation for LLM models.

This module re-exports from the centralized model registry.
For adding new models, edit: zwarm/core/registry.py

Backwards-compatible API preserved for existing code.
"""

from __future__ import annotations

# Re-export everything from registry for backwards compatibility
from zwarm.core.registry import (
    ModelInfo,
    MODELS,
    resolve_model,
    get_adapter_for_model,
    get_default_model,
    list_models,
    list_adapters,
    get_models_help_text,
    get_models_table_data,
    estimate_cost,
    format_cost,
    estimate_session_cost,
)

# Backwards compatibility alias
ModelPricing = ModelInfo

# Legacy aliases for backwards compatibility
MODEL_PRICING = {m.canonical: m for m in MODELS}
MODEL_ALIASES = {}
for m in MODELS:
    for alias in m.aliases:
        MODEL_ALIASES[alias] = m.canonical


def get_pricing(model: str) -> ModelInfo | None:
    """
    Get pricing for a model.

    Args:
        model: Model name or alias

    Returns:
        ModelInfo or None if unknown
    """
    return resolve_model(model)


__all__ = [
    # New API
    "ModelInfo",
    "MODELS",
    "resolve_model",
    "get_adapter_for_model",
    "get_default_model",
    "list_models",
    "list_adapters",
    "get_models_help_text",
    "get_models_table_data",
    "estimate_cost",
    "format_cost",
    "estimate_session_cost",
    # Legacy API
    "MODEL_PRICING",
    "MODEL_ALIASES",
    "ModelPricing",
    "get_pricing",
]
