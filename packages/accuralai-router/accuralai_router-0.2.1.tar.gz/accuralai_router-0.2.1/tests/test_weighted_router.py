import pytest

from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest

from accuralai_router.strategies.weighted import build_weighted_router


@pytest.mark.anyio
async def test_weighted_router_filters_unhealthy_backends():
    router = await build_weighted_router(
        config={
            "backends": [
                {"backend_id": "primary", "weight": 0.1},
                {"backend_id": "secondary", "weight": 0.9},
            ],
        },
        health_check=lambda backend: backend == "secondary",
    )
    request = GenerateRequest(prompt="ping")
    selected = await router.route(request)
    assert selected == "secondary"


@pytest.mark.anyio
async def test_weighted_router_enforces_capacity_limits():
    router = await build_weighted_router(
        config={
            "backends": [
                {"backend_id": "limited", "weight": 1.0, "capacity": 1},
            ],
        }
    )
    request = GenerateRequest(prompt="hello")
    assert await router.route(request) == "limited"
    with pytest.raises(ConfigurationError):
        await router.route(request)
