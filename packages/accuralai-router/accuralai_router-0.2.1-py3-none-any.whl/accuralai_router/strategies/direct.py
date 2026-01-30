"""Direct router implementation."""

from __future__ import annotations

from typing import Any, Mapping

from accuralai_core.config.schema import RouterSettings
from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Router

from ..base import HealthCheck, RouterContext, RouterMetricsRecorder
from ..config import DirectRouterOptions, parse_options


class DirectRouter(Router):
    """Router that honours explicit route hints or defaults."""

    def __init__(
        self,
        *,
        options: DirectRouterOptions,
        context: RouterContext,
    ) -> None:
        self._options = options
        self._context = context

    async def route(self, request: GenerateRequest) -> str:
        hint = (request.route_hint or "").strip()
        metrics = self._context.metrics_recorder()

        if hint:
            if self._context.is_backend_healthy(hint) or self._options.allow_unknown:
                metrics.record_decision(
                    router_id=self._context.router_id,
                    backend_id=hint,
                    reason="hint",
                    request=request,
                )
                return hint
            msg = f"Backend '{hint}' is marked unhealthy by health checks."
            raise ConfigurationError(msg)

        backend_id = self._options.default_backend
        metrics.record_decision(
            router_id=self._context.router_id,
            backend_id=backend_id,
            reason="default",
            request=request,
        )
        return backend_id


async def build_direct_router(
    *,
    config: RouterSettings | Mapping[str, Any] | None = None,
    context: RouterContext | None = None,
    health_check: HealthCheck | None = None,
    metrics: RouterMetricsRecorder | None = None,
    router_id: str = "router.direct",
    **_: Any,
) -> Router:
    """Factory registered via entry point for the direct router."""
    options_payload: Mapping[str, Any] | DirectRouterOptions | None = None
    if isinstance(config, RouterSettings):
        options_payload = config.options or {"default_backend": config.default_backend or "mock"}
        if not options_payload.get("default_backend"):
            options_payload["default_backend"] = config.default_backend or "mock"
    else:
        options_payload = config

    options = parse_options(DirectRouterOptions, options_payload)
    resolved_context = context or RouterContext(router_id=router_id, health_check=health_check, metrics=metrics)
    return DirectRouter(options=options, context=resolved_context)
