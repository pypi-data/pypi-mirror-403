import pytest

from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest

from accuralai_router.strategies.direct import build_direct_router


@pytest.mark.anyio
async def test_direct_router_prefers_route_hint():
    router = await build_direct_router(
        config={"default_backend": "mock"},
        health_check=lambda backend: True,
        router_id="router.test",
    )
    request = GenerateRequest(prompt="hello", route_hint="primary")
    selected = await router.route(request)
    assert selected == "primary"


@pytest.mark.anyio
async def test_direct_router_uses_default_when_no_hint():
    router = await build_direct_router(config={"default_backend": "mock"})
    request = GenerateRequest(prompt="hello")
    selected = await router.route(request)
    assert selected == "mock"


@pytest.mark.anyio
async def test_direct_router_rejects_unhealthy_hint():
    router = await build_direct_router(
        config={"default_backend": "mock"},
        health_check=lambda backend: backend != "downstream",
    )
    request = GenerateRequest(prompt="hello", route_hint="downstream")
    with pytest.raises(ConfigurationError):
        await router.route(request)


@pytest.mark.anyio
async def test_direct_router_allows_unknown_override():
    router = await build_direct_router(
        config={"default_backend": "mock", "allow_unknown": True},
        health_check=lambda backend: False,
    )
    request = GenerateRequest(prompt="hello", route_hint="mystery")
    selected = await router.route(request)
    assert selected == "mystery"
