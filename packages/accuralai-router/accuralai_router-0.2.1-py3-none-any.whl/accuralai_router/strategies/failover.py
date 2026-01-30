"""Failover routing strategy."""

from __future__ import annotations

import time
from typing import Any, Dict, Mapping

from accuralai_core.config.schema import RouterSettings
from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Router

from ..base import HealthCheck, RouterContext, RouterMetricsRecorder
from ..config import FailoverRouterOptions, parse_options


class FailoverRouter(Router):
    """Router that prefers a primary backend with ordered fallbacks."""

    def __init__(
        self,
        *,
        options: FailoverRouterOptions,
        context: RouterContext,
    ) -> None:
        self._options = options
        self._context = context
        self._cooldowns: Dict[str, float] = {}

    async def route(self, request: GenerateRequest) -> str:
        now = time.monotonic()
        for index, backend_id in enumerate(self._options.ordered_backends):
            cooldown_until = self._cooldowns.get(backend_id)
            healthy = self._context.is_backend_healthy(backend_id)
            if healthy:
                if cooldown_until:
                    self._cooldowns.pop(backend_id, None)
                reason = "primary" if index == 0 else "fallback"
                self._context.metrics_recorder().record_decision(
                    router_id=self._context.router_id,
                    backend_id=backend_id,
                    reason=reason,
                    request=request,
                )
                return backend_id

            # Backend unhealthy; respect cooldown to avoid repeated checks.
            if not cooldown_until or cooldown_until <= now:
                self._cooldowns[backend_id] = now + self._options.recheck_interval_s

        msg = "Failover router could not find a healthy backend."
        raise ConfigurationError(msg)


async def build_failover_router(
    *,
    config: RouterSettings | Mapping[str, Any] | None = None,
    context: RouterContext | None = None,
    health_check: HealthCheck | None = None,
    metrics: RouterMetricsRecorder | None = None,
    router_id: str = "router.failover",
    **_: Any,
) -> Router:
    """Factory registered via entry point for the failover router."""
    options_payload: Mapping[str, Any] | FailoverRouterOptions | None = None
    if isinstance(config, RouterSettings):
        payload: Dict[str, Any] = dict(config.options or {})
        payload.setdefault("primary", config.default_backend or "mock")
        options_payload = payload
    else:
        options_payload = config

    options = parse_options(FailoverRouterOptions, options_payload)
    resolved_context = context or RouterContext(router_id=router_id, health_check=health_check, metrics=metrics)
    return FailoverRouter(options=options, context=resolved_context)
