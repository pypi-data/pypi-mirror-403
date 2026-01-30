"""Rules-based routing strategy."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping, Sequence

from accuralai_core.config.schema import RouterSettings
from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Router

from ..base import HealthCheck, RouterContext, RouterMetricsRecorder
from ..config import (
    RuleConfig,
    RulePredicate,
    RulesRouterOptions,
    parse_options,
)


class RulesRouter(Router):
    """Router that matches request metadata against configured rules."""

    def __init__(
        self,
        *,
        options: RulesRouterOptions,
        context: RouterContext,
    ) -> None:
        self._options = options
        self._context = context
        self._regex_cache: Dict[str, re.Pattern[str]] = {}

    async def route(self, request: GenerateRequest) -> str:
        for index, rule in enumerate(self._options.rules):
            if self._matches(rule, request):
                backend_id = rule.backend
                if not self._context.is_backend_healthy(backend_id):
                    continue
                self._context.metrics_recorder().record_decision(
                    router_id=self._context.router_id,
                    backend_id=backend_id,
                    reason=f"rule:{rule.rule_id or index}",
                    request=request,
                )
                return backend_id

        if self._options.default_backend:
            backend_id = self._options.default_backend
            if self._context.is_backend_healthy(backend_id):
                self._context.metrics_recorder().record_decision(
                    router_id=self._context.router_id,
                    backend_id=backend_id,
                    reason="default",
                    request=request,
                )
                return backend_id

        msg = "Rules router could not select a backend."
        raise ConfigurationError(msg)

    def _matches(self, rule: RuleConfig, request: GenerateRequest) -> bool:
        return all(self._match_predicate(predicate, request) for predicate in rule.predicates)

    def _match_predicate(self, predicate: RulePredicate, request: GenerateRequest) -> bool:
        source = predicate.source
        if source == "tags":
            return self._match_tags(predicate, request.tags)
        if source == "metadata":
            return self._match_mapping(predicate, request.metadata)
        if source == "parameters":
            return self._match_mapping(predicate, request.parameters)
        return False

    def _match_tags(self, predicate: RulePredicate, tags: Sequence[str]) -> bool:
        tags_lower = {tag.lower() for tag in tags}
        expected = predicate.value
        if predicate.operator == "eq":
            return isinstance(expected, str) and expected.lower() in tags_lower
        if predicate.operator == "in":
            if isinstance(expected, (list, tuple, set)):
                return any(isinstance(item, str) and item.lower() in tags_lower for item in expected)
            if isinstance(expected, str):
                return expected.lower() in tags_lower
            return False
        if predicate.operator == "regex":
            if not isinstance(expected, str):
                return False
            pattern = self._compile_regex(expected)
            return any(pattern.search(tag) for tag in tags)
        return False

    def _match_mapping(self, predicate: RulePredicate, mapping: Mapping[str, Any]) -> bool:
        key = predicate.key or ""
        if key not in mapping:
            return False
        value = mapping.get(key)
        op = predicate.operator
        expected = predicate.value

        if op == "eq":
            return value == expected
        if op == "in":
            if isinstance(expected, Iterable) and not isinstance(expected, (str, bytes)):
                return value in expected
            return value == expected
        if op in {"gte", "lte"}:
            try:
                actual_num = float(value)  # type: ignore[arg-type]
                expected_num = float(expected)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False
            return actual_num >= expected_num if op == "gte" else actual_num <= expected_num
        if op == "regex":
            if not isinstance(expected, str):
                return False
            pattern = self._compile_regex(expected)
            return bool(isinstance(value, str) and pattern.search(value))
        return False

    def _compile_regex(self, pattern: str) -> re.Pattern[str]:
        cached = self._regex_cache.get(pattern)
        if cached:
            return cached
        compiled = re.compile(pattern, re.IGNORECASE)
        self._regex_cache[pattern] = compiled
        return compiled


async def build_rules_router(
    *,
    config: RouterSettings | Mapping[str, Any] | None = None,
    context: RouterContext | None = None,
    health_check: HealthCheck | None = None,
    metrics: RouterMetricsRecorder | None = None,
    router_id: str = "router.rules",
    **_: Any,
) -> Router:
    """Factory registered via entry point for the rules router."""
    options_payload: Mapping[str, Any] | RulesRouterOptions | None = None
    if isinstance(config, RouterSettings):
        options_payload = config.options or {}
        if config.default_backend and "default_backend" not in options_payload:
            options_payload["default_backend"] = config.default_backend
    else:
        options_payload = config

    options = parse_options(RulesRouterOptions, options_payload)
    resolved_context = context or RouterContext(router_id=router_id, health_check=health_check, metrics=metrics)
    return RulesRouter(options=options, context=resolved_context)
