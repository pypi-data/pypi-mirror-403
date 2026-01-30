"""Weighted routing strategy."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Mapping, Optional

from accuralai_core.config.schema import RouterSettings
from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Router

from ..base import HealthCheck, RouterContext, RouterMetricsRecorder
from ..config import WeightedBackendConfig, WeightedRouterOptions, parse_options


class WeightedRouter(Router):
    """Probabilistic router that distributes traffic by weight."""

    def __init__(
        self,
        *,
        options: WeightedRouterOptions,
        context: RouterContext,
    ) -> None:
        self._options = options
        self._context = context
        self._random = random.Random(options.seed)
        self._capacities: Dict[str, Optional[int]] = {
            backend.backend_id: backend.capacity for backend in options.backends
        }

    async def route(self, request: GenerateRequest) -> str:
        available = self._eligible_backends()
        if not available:
            msg = "No eligible backends available for weighted routing."
            raise ConfigurationError(msg)

        population: List[str] = [backend.backend_id for backend in available]
        weights: List[float] = [backend.weight for backend in available]

        backend_id = self._random.choices(population=population, weights=weights, k=1)[0]
        self._decrement_capacity(backend_id)

        self._context.metrics_recorder().record_decision(
            router_id=self._context.router_id,
            backend_id=backend_id,
            reason="weighted",
            request=request,
            extra={"weights": dict(zip(population, weights, strict=False))},
        )
        return backend_id

    def _eligible_backends(self) -> List[WeightedBackendConfig]:
        healthy: List[WeightedBackendConfig] = []
        for backend in self._options.backends:
            capacity = self._capacities.get(backend.backend_id)
            if capacity is not None and capacity <= 0:
                continue
            if not self._context.is_backend_healthy(backend.backend_id):
                continue
            healthy.append(backend)
        return healthy

    def _decrement_capacity(self, backend_id: str) -> None:
        capacity = self._capacities.get(backend_id)
        if capacity is None:
            return
        self._capacities[backend_id] = max(0, capacity - 1)


async def build_weighted_router(
    *,
    config: RouterSettings | Mapping[str, Any] | None = None,
    context: RouterContext | None = None,
    health_check: HealthCheck | None = None,
    metrics: RouterMetricsRecorder | None = None,
    router_id: str = "router.weighted",
    **_: Any,
) -> Router:
    """Factory registered via entry point for the weighted router."""
    options_payload: Mapping[str, Any] | WeightedRouterOptions | None = None
    if isinstance(config, RouterSettings):
        options_payload = config.options or {}
    else:
        options_payload = config

    options = parse_options(WeightedRouterOptions, options_payload)
    resolved_context = context or RouterContext(router_id=router_id, health_check=health_check, metrics=metrics)
    return WeightedRouter(options=options, context=resolved_context)
