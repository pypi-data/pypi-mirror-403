"""
Model Registry - Centralized LLM model definitions for zwarm.

This registry defines all supported models with:
- Canonical names and aliases
- Adapter mapping (which CLI handles the model)
- Pricing information

Add new models here and they'll automatically appear in:
- `zwarm interactive` help and `models` command
- Cost estimation
- Adapter auto-detection from model name
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelInfo:
    """Complete information about an LLM model."""

    # Identity
    canonical: str  # Full model name (e.g., "gpt-5.1-codex-mini")
    adapter: str  # "codex" or "claude"
    aliases: list[str] = field(default_factory=list)  # Short names

    # Pricing ($ per million tokens)
    input_per_million: float = 0.0
    output_per_million: float = 0.0
    cached_input_per_million: float | None = None

    # Metadata
    description: str = ""
    is_default: bool = False  # Default model for this adapter

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        """Estimate cost in dollars."""
        input_cost = (input_tokens / 1_000_000) * self.input_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_per_million

        cached_cost = 0.0
        if cached_tokens and self.cached_input_per_million:
            cached_cost = (cached_tokens / 1_000_000) * self.cached_input_per_million

        return input_cost + output_cost + cached_cost


# =============================================================================
# Model Registry - ADD NEW MODELS HERE
# =============================================================================

MODELS: list[ModelInfo] = [
    # -------------------------------------------------------------------------
    # OpenAI Codex Models (via `codex` CLI)
    # -------------------------------------------------------------------------
    ModelInfo(
        canonical="gpt-5.1-codex-mini",
        adapter="codex",
        aliases=["codex-mini", "mini"],
        input_per_million=0.25,
        output_per_million=2.00,
        cached_input_per_million=0.025,
        description="Fast, cost-effective coding model",
        is_default=True,
    ),
    ModelInfo(
        canonical="gpt-5.1-codex",
        adapter="codex",
        aliases=["codex", "codex-full"],
        input_per_million=1.25,
        output_per_million=10.00,
        cached_input_per_million=0.125,
        description="Full Codex model with extended reasoning",
    ),
    ModelInfo(
        canonical="gpt-5.1-codex-max",
        adapter="codex",
        aliases=["codex-max", "max"],
        input_per_million=1.25,
        output_per_million=10.00,
        cached_input_per_million=0.125,
        description="Maximum context Codex model",
    ),
    # -------------------------------------------------------------------------
    # Anthropic Claude Models (via `claude` CLI)
    # -------------------------------------------------------------------------
    ModelInfo(
        canonical="sonnet",
        adapter="claude",
        aliases=["claude-sonnet", "claude-4-sonnet"],
        input_per_million=3.00,
        output_per_million=15.00,
        description="Balanced Claude model for most tasks",
        is_default=True,
    ),
    ModelInfo(
        canonical="opus",
        adapter="claude",
        aliases=["claude-opus", "claude-4-opus"],
        input_per_million=15.00,
        output_per_million=75.00,
        description="Most capable Claude model",
    ),
    ModelInfo(
        canonical="haiku",
        adapter="claude",
        aliases=["claude-haiku", "claude-4-haiku"],
        input_per_million=0.25,
        output_per_million=1.25,
        description="Fast, lightweight Claude model",
    ),
]


# =============================================================================
# Registry Lookups
# =============================================================================


def _build_lookup_tables() -> tuple[dict[str, ModelInfo], dict[str, ModelInfo]]:
    """Build lookup tables for fast model resolution."""
    by_canonical: dict[str, ModelInfo] = {}
    by_alias: dict[str, ModelInfo] = {}

    for model in MODELS:
        by_canonical[model.canonical.lower()] = model
        by_alias[model.canonical.lower()] = model
        for alias in model.aliases:
            by_alias[alias.lower()] = model

    return by_canonical, by_alias


_BY_CANONICAL, _BY_ALIAS = _build_lookup_tables()


def resolve_model(name: str) -> ModelInfo | None:
    """
    Resolve a model name or alias to its ModelInfo.

    Args:
        name: Model name, alias, or partial match

    Returns:
        ModelInfo or None if not found
    """
    name_lower = name.lower()

    # Exact match on alias or canonical
    if name_lower in _BY_ALIAS:
        return _BY_ALIAS[name_lower]

    # Prefix match (e.g., "gpt-5.1-codex-mini-2026-01" -> "gpt-5.1-codex-mini")
    for canonical, model in _BY_CANONICAL.items():
        if name_lower.startswith(canonical):
            return model

    return None


def get_adapter_for_model(name: str) -> str | None:
    """
    Get the adapter name for a model.

    Args:
        name: Model name or alias

    Returns:
        Adapter name ("codex" or "claude") or None if unknown
    """
    model = resolve_model(name)
    return model.adapter if model else None


def get_default_model(adapter: str) -> str | None:
    """
    Get the default model for an adapter.

    Args:
        adapter: Adapter name ("codex" or "claude")

    Returns:
        Default model canonical name or None
    """
    for model in MODELS:
        if model.adapter == adapter and model.is_default:
            return model.canonical
    return None


def list_models(adapter: str | None = None) -> list[ModelInfo]:
    """
    List available models.

    Args:
        adapter: Filter by adapter, or None for all

    Returns:
        List of ModelInfo objects
    """
    if adapter:
        return [m for m in MODELS if m.adapter == adapter]
    return MODELS.copy()


def list_adapters() -> list[str]:
    """Get list of unique adapter names."""
    return sorted(set(m.adapter for m in MODELS))


def get_models_help_text() -> str:
    """
    Generate help text showing all available models.

    Returns formatted string for display in help messages.
    """
    lines = ["", "Available models:"]

    for adapter in list_adapters():
        lines.append(f"\n  {adapter.upper()}:")
        for model in list_models(adapter):
            default_marker = " *" if model.is_default else ""
            aliases = ", ".join(model.aliases) if model.aliases else ""
            alias_str = f" ({aliases})" if aliases else ""

            lines.append(f"    {model.canonical}{alias_str}{default_marker}")

    lines.append("\n  * = default for adapter")
    return "\n".join(lines)


def get_models_table_data() -> list[dict[str, Any]]:
    """
    Get model data formatted for table display.

    Returns list of dicts with keys: adapter, model, aliases, default, price, description
    """
    data = []
    for model in MODELS:
        data.append({
            "adapter": model.adapter,
            "model": model.canonical,
            "aliases": ", ".join(model.aliases),
            "default": model.is_default,
            "input_price": model.input_per_million,
            "output_price": model.output_per_million,
            "description": model.description,
        })
    return data


# =============================================================================
# Cost Estimation
# =============================================================================


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> float | None:
    """
    Estimate cost for a model run.

    Args:
        model: Model name or alias
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cached_tokens: Number of cached input tokens

    Returns:
        Cost in USD, or None if model unknown
    """
    model_info = resolve_model(model)
    if model_info is None:
        return None

    return model_info.estimate_cost(input_tokens, output_tokens, cached_tokens)


def format_cost(cost: float | None) -> str:
    """Format cost as a human-readable string."""
    if cost is None:
        return "?"
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1.00:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def estimate_session_cost(
    model: str,
    token_usage: dict[str, Any],
) -> dict[str, Any]:
    """
    Estimate cost for a session given its token usage.

    Args:
        model: Model used
        token_usage: Dict with input_tokens, output_tokens, etc.

    Returns:
        Dict with cost info: {cost, cost_formatted, pricing_known, ...}
    """
    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)
    cached_tokens = token_usage.get("cached_tokens", 0)

    cost = estimate_cost(model, input_tokens, output_tokens, cached_tokens)

    return {
        "cost": cost,
        "cost_formatted": format_cost(cost),
        "pricing_known": cost is not None,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
