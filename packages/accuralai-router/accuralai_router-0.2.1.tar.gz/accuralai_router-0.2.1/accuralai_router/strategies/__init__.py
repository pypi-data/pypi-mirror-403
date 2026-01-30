"""Routing strategy implementations."""

from .direct import build_direct_router
from .failover import build_failover_router
from .rules import build_rules_router
from .weighted import build_weighted_router

__all__ = [
    "build_direct_router",
    "build_failover_router",
    "build_rules_router",
    "build_weighted_router",
]
