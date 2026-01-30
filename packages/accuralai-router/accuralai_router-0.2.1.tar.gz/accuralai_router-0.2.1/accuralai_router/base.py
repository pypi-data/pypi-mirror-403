"""Shared primitives for router implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Protocol

from accuralai_core.contracts.models import GenerateRequest


HealthCheck = Callable[[str], bool]


class RouterMetricsRecorder(Protocol):
    """Protocol describing minimal metrics hooks for routers."""

    def record_decision(
        self,
        *,
        router_id: str,
        backend_id: str,
        reason: str,
        request: Optional[GenerateRequest] = None,
        extra: Optional[Dict[str, object]] = None,
    ) -> None:
        """Record a routing decision for observability."""

    def record_error(
        self,
        *,
        router_id: str,
        backend_id: str,
        error: Exception,
        request: Optional[GenerateRequest] = None,
    ) -> None:
        """Record routing-related errors (best-effort)."""


class NullRouterMetricsRecorder:
    """Fallback metrics recorder when none is provided."""

    def record_decision(
        self,
        *,
        router_id: str,
        backend_id: str,
        reason: str,
        request: Optional[GenerateRequest] = None,
        extra: Optional[Dict[str, object]] = None,
    ) -> None:
        return None

    def record_error(
        self,
        *,
        router_id: str,
        backend_id: str,
        error: Exception,
        request: Optional[GenerateRequest] = None,
    ) -> None:
        return None


def resolve_metrics(metrics: RouterMetricsRecorder | None) -> RouterMetricsRecorder:
    """Return a usable metrics recorder."""
    if metrics is None:
        return NullRouterMetricsRecorder()
    return metrics


@dataclass(slots=True)
class RouterContext:
    """Container for dependencies shared across router implementations."""

    router_id: str
    health_check: Optional[HealthCheck] = None
    metrics: RouterMetricsRecorder | None = None

    def is_backend_healthy(self, backend_id: str) -> bool:
        """Return whether the backend is considered healthy."""
        if not self.health_check:
            return True
        try:
            return self.health_check(backend_id)
        except Exception as error:  # pragma: no cover - defensive guardrail
            metrics = resolve_metrics(self.metrics)
            metrics.record_error(
                router_id=self.router_id,
                backend_id=backend_id,
                error=error,
                request=None,
            )
            return True

    def metrics_recorder(self) -> RouterMetricsRecorder:
        """Return an active metrics recorder."""
        return resolve_metrics(self.metrics)
