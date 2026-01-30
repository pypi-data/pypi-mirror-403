"""Routing strategies for AccuralAI."""

from __future__ import annotations

from .strategies.direct import build_direct_router
from .strategies.failover import build_failover_router
from .strategies.rules import build_rules_router
from .strategies.weighted import build_weighted_router
from .strategies.complexity import build_complexity_router

__all__ = [
    "build_direct_router",
    "build_weighted_router",
    "build_failover_router",
    "build_rules_router",
    "build_complexity_router",
]
