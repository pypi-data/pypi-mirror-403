"""Complexity-based routing strategy."""

from __future__ import annotations

from typing import Any, Dict, Literal, Mapping, Optional

from accuralai_core.config.schema import RouterSettings
from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Router
from accuralai_core.utils.tokenizer import DEFAULT_TOKENIZER

from ..base import HealthCheck, RouterContext, RouterMetricsRecorder
from ..config import (
    ComplexityRouterOptions,
    ComplexityTierConfig,
    parse_options,
)


class ComplexityRouter(Router):
    """Router that selects backends based on request complexity scoring."""

    def __init__(
        self,
        *,
        options: ComplexityRouterOptions,
        context: RouterContext,
    ) -> None:
        self._options = options
        self._context = context
        self._tokenizer = DEFAULT_TOKENIZER
        self._tier_map: Dict[str, ComplexityTierConfig] = {
            tier.tier: tier for tier in options.tiers
        }

    async def route(self, request: GenerateRequest) -> str:
        # Check for explicit complexity metadata first
        if self._options.honor_explicit_complexity:
            explicit_complexity = request.metadata.get("complexity")
            if explicit_complexity in {"low", "medium", "high"}:
                model = self._select_model_for_tier(explicit_complexity)
                if model:
                    # Set the model in request parameters for the backend to use
                    request.parameters["model"] = model
                    self._context.metrics_recorder().record_decision(
                        router_id=self._context.router_id,
                        backend_id=self._options.backend_id,
                        reason="explicit_complexity",
                        request=request,
                        extra={"complexity": explicit_complexity, "model": model},
                    )
                    return self._options.backend_id

        # Calculate complexity score
        score = self._calculate_complexity_score(request)
        tier = self._determine_tier(score)

        # Select model for the determined tier
        model = self._select_model_for_tier(tier)
        if model:
            # Set the model in request parameters for the backend to use
            request.parameters["model"] = model
            self._context.metrics_recorder().record_decision(
                router_id=self._context.router_id,
                backend_id=self._options.backend_id,
                reason="complexity_score",
                request=request,
                extra={"score": score, "tier": tier, "model": model},
            )
            return self._options.backend_id

        # Fallback to default backend without model override
        self._context.metrics_recorder().record_decision(
            router_id=self._context.router_id,
            backend_id=self._options.backend_id,
            reason="fallback",
            request=request,
            extra={"score": score, "tier": tier},
        )
        return self._options.backend_id

    def _calculate_complexity_score(self, request: GenerateRequest) -> float:
        """Calculate weighted complexity score for the request."""
        scoring = self._options.scoring
        score = 0.0

        # Token-based complexity (prompt + system_prompt + history)
        token_count = self._tokenizer.count_request_tokens(request)
        score += token_count * scoring.token_weight

        # History depth complexity
        history_turns = len(request.history)
        score += history_turns * scoring.history_weight

        # Tool presence complexity
        if request.tools:
            score += scoring.tool_weight

        # Parameter complexity
        param_complexity = self._calculate_parameter_complexity(request.parameters)
        score += param_complexity * scoring.parameter_complexity_weight

        return score

    def _calculate_parameter_complexity(self, parameters: Dict[str, Any]) -> float:
        """Calculate complexity score based on generation parameters."""
        complexity = 0.0

        # Temperature extremes indicate more complex generation
        temperature = parameters.get("temperature")
        if temperature is not None:
            if temperature < 0.1 or temperature > 0.9:
                complexity += 1.0

        # Advanced sampling parameters
        if "top_k" in parameters or "top_p" in parameters:
            complexity += 0.5

        # Long generation parameters
        max_tokens = parameters.get("max_tokens") or parameters.get("max_tokens_to_sample")
        if max_tokens and max_tokens > 1000:
            complexity += 0.5

        # Custom parameters indicate complexity
        custom_params = set(parameters.keys()) - {
            "temperature", "top_k", "top_p", "max_tokens", "max_tokens_to_sample",
            "stop", "stream", "seed"
        }
        complexity += len(custom_params) * 0.2

        return complexity

    def _determine_tier(self, score: float) -> Literal["low", "medium", "high"]:
        """Determine complexity tier based on score and tier-specific thresholds."""
        # Check tier-specific thresholds first
        for tier_name in ["high", "medium", "low"]:
            tier_config = self._tier_map.get(tier_name)
            if not tier_config:
                continue

            min_score = tier_config.min_score
            max_score = tier_config.max_score

            if min_score is not None and max_score is not None:
                if min_score <= score <= max_score:
                    return tier_name
            elif min_score is not None and score >= min_score:
                return tier_name
            elif max_score is not None and score <= max_score:
                return tier_name

        # Fall back to global thresholds
        if score < self._options.low_threshold:
            return "low"
        elif score >= self._options.high_threshold:
            return "high"
        else:
            return "medium"

    def _select_model_for_tier(self, tier: str) -> Optional[str]:
        """Select the first model for the given tier."""
        tier_config = self._tier_map.get(tier)
        if not tier_config:
            return None

        # Return the first model in the tier's model list
        return tier_config.models[0] if tier_config.models else None


async def build_complexity_router(
    *,
    config: RouterSettings | Mapping[str, Any] | None = None,
    context: RouterContext | None = None,
    health_check: HealthCheck | None = None,
    metrics: RouterMetricsRecorder | None = None,
    router_id: str = "router.complexity",
    **_: Any,
) -> Router:
    """Factory registered via entry point for the complexity router."""
    options_payload: Mapping[str, Any] | ComplexityRouterOptions | None = None
    if isinstance(config, RouterSettings):
        options_payload = config.options or {}
        if config.default_backend and "backend_id" not in options_payload:
            options_payload["backend_id"] = config.default_backend
    else:
        options_payload = config

    options = parse_options(ComplexityRouterOptions, options_payload)
    resolved_context = context or RouterContext(router_id=router_id, health_check=health_check, metrics=metrics)
    return ComplexityRouter(options=options, context=resolved_context)
