import pytest

from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest

from accuralai_router.strategies.rules import build_rules_router


@pytest.mark.anyio
async def test_rules_router_matches_tag_regex():
    router = await build_rules_router(
        config={
            "rules": [
                {
                    "backend": "finance-backend",
                    "predicates": [
                        {"source": "tags", "operator": "regex", "value": r"fin.*"},
                    ],
                }
            ],
            "default_backend": "general",
        },
    )
    request = GenerateRequest(prompt="hello", tags=["Finance"])
    assert await router.route(request) == "finance-backend"


@pytest.mark.anyio
async def test_rules_router_applies_metadata_threshold():
    router = await build_rules_router(
        config={
            "rules": [
                {
                    "rule_id": "high_latency",
                    "backend": "slow-lane",
                    "predicates": [
                        {"source": "metadata", "key": "latency_ms", "operator": "gte", "value": 100},
                    ],
                },
                {
                    "backend": "default-fast",
                    "predicates": [
                        {"source": "metadata", "key": "latency_ms", "operator": "lte", "value": 99},
                    ],
                },
            ],
        },
        health_check=lambda backend: True,
    )
    request = GenerateRequest(prompt="hello", metadata={"latency_ms": 150})
    assert await router.route(request) == "slow-lane"


@pytest.mark.anyio
async def test_rules_router_uses_default_when_no_rule_matches():
    router = await build_rules_router(
        config={
            "rules": [],
            "default_backend": "fallback",
        }
    )
    request = GenerateRequest(prompt="hello", tags=["misc"])
    assert await router.route(request) == "fallback"


@pytest.mark.anyio
async def test_rules_router_raises_without_default():
    router = await build_rules_router(
        config={
            "rules": [
                {
                    "backend": "restricted",
                    "predicates": [{"source": "tags", "operator": "eq", "value": "vip"}],
                }
            ],
        }
    )
    request = GenerateRequest(prompt="hello", tags=["general"])
    with pytest.raises(ConfigurationError):
        await router.route(request)
