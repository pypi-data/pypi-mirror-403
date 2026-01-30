import pytest

from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest

from accuralai_router.strategies.failover import build_failover_router


@pytest.mark.anyio
async def test_failover_router_uses_primary_when_healthy():
    router = await build_failover_router(
        config={"primary": "primary", "fallbacks": ["backup"]},
        health_check=lambda backend: backend == "primary",
    )
    request = GenerateRequest(prompt="status")
    assert await router.route(request) == "primary"


@pytest.mark.anyio
async def test_failover_router_falls_back_when_primary_unhealthy():
    health_state = {"primary": False, "backup": True}

    def health_check(backend: str) -> bool:
        return health_state.get(backend, False)

    router = await build_failover_router(
        config={"primary": "primary", "fallbacks": ["backup"]},
        health_check=health_check,
        router_id="router.failover-test",
    )
    request = GenerateRequest(prompt="status")
    assert await router.route(request) == "backup"

    # Mark primary healthy again and ensure router returns to it.
    health_state["primary"] = True
    assert await router.route(request) == "primary"


@pytest.mark.anyio
async def test_failover_router_raises_when_no_backends_available():
    router = await build_failover_router(
        config={"primary": "primary", "fallbacks": ["backup"]},
        health_check=lambda backend: False,
    )
    request = GenerateRequest(prompt="status")
    with pytest.raises(ConfigurationError):
        await router.route(request)
