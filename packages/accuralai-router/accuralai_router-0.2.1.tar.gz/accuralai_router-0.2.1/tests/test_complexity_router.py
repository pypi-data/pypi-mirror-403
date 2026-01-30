"""Tests for complexity router implementation."""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from accuralai_core.contracts.models import GenerateRequest

from accuralai_router.strategies.complexity import ComplexityRouter, build_complexity_router
from accuralai_router.config import (
    ComplexityRouterOptions,
    ComplexityScoringConfig,
    ComplexityTierConfig,
)
from accuralai_router.base import RouterContext


@pytest.fixture
def mock_context():
    """Create a mock router context."""
    context = Mock(spec=RouterContext)
    context.router_id = "test-router"
    context.is_backend_healthy = Mock(return_value=True)
    context.metrics_recorder = Mock()
    context.metrics_recorder.return_value.record_decision = Mock()
    return context


@pytest.fixture
def basic_options():
    """Create basic complexity router options."""
    return ComplexityRouterOptions(
        tiers=[
            ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
            ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
            ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"]),
        ],
        low_threshold=50.0,
        high_threshold=200.0,
        backend_id="google",
    )


@pytest.fixture
def router(basic_options, mock_context):
    """Create a complexity router instance."""
    return ComplexityRouter(options=basic_options, context=mock_context)


class TestComplexityScoring:
    """Test complexity score calculation."""

    def test_simple_prompt_scoring(self, router):
        """Test scoring for simple prompts."""
        request = GenerateRequest(prompt="Hello world")
        score = router._calculate_complexity_score(request)
        # Simple prompt should have low score (around 2-3 tokens)
        assert score < 10.0

    def test_long_prompt_scoring(self, router):
        """Test scoring for long prompts."""
        long_prompt = "This is a very long prompt. " * 50  # ~1500 characters
        request = GenerateRequest(prompt=long_prompt)
        score = router._calculate_complexity_score(request)
        # Long prompt should have high score
        assert score > 100.0

    def test_system_prompt_scoring(self, router):
        """Test scoring includes system prompt."""
        request = GenerateRequest(
            prompt="Hello",
            system_prompt="You are a helpful assistant. " * 20
        )
        score = router._calculate_complexity_score(request)
        # Should include system prompt tokens
        assert score > 20.0

    def test_history_scoring(self, router):
        """Test scoring includes conversation history."""
        request = GenerateRequest(
            prompt="Hello",
            history=[
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "First response"},
                {"role": "user", "content": "Second message"},
            ]
        )
        score = router._calculate_complexity_score(request)
        # Should include history weight (3 turns * 2.0 = 6.0)
        assert score > 6.0

    def test_tools_scoring(self, router):
        """Test scoring includes tool presence."""
        request = GenerateRequest(
            prompt="Hello",
            tools=[{"name": "search", "description": "Search the web"}]
        )
        score = router._calculate_complexity_score(request)
        # Should include tool weight (10.0)
        assert score >= 10.0

    def test_parameter_complexity_scoring(self, router):
        """Test scoring includes parameter complexity."""
        request = GenerateRequest(
            prompt="Hello",
            parameters={
                "temperature": 0.1,  # Extreme temperature
                "top_k": 40,  # Advanced parameter
                "max_tokens": 2000,  # Long generation
                "custom_param": "value",  # Custom parameter
            }
        )
        score = router._calculate_complexity_score(request)
        # Should include parameter complexity
        assert score > 5.0

    def test_custom_scoring_weights(self):
        """Test custom scoring weights."""
        custom_scoring = ComplexityScoringConfig(
            token_weight=2.0,
            history_weight=5.0,
            tool_weight=20.0,
            parameter_complexity_weight=10.0,
        )
        options = ComplexityRouterOptions(
            tiers=[
                ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
                ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
                ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"]),
            ],
            scoring=custom_scoring,
            backend_id="google",
        )
        context = Mock(spec=RouterContext)
        context.router_id = "test"
        context.is_backend_healthy = Mock(return_value=True)
        context.metrics_recorder = Mock()
        context.metrics_recorder.return_value.record_decision = Mock()
        
        router = ComplexityRouter(options=options, context=context)
        
        request = GenerateRequest(
            prompt="Hello",
            history=[{"role": "user", "content": "Test"}],
            tools=[{"name": "test"}],
        )
        score = router._calculate_complexity_score(request)
        # Should use custom weights
        assert score > 20.0  # tool_weight


class TestTierDetermination:
    """Test tier determination logic."""

    def test_low_tier_determination(self, router):
        """Test low tier determination."""
        assert router._determine_tier(25.0) == "low"
        assert router._determine_tier(49.9) == "low"

    def test_medium_tier_determination(self, router):
        """Test medium tier determination."""
        assert router._determine_tier(50.0) == "medium"
        assert router._determine_tier(100.0) == "medium"
        assert router._determine_tier(199.9) == "medium"

    def test_high_tier_determination(self, router):
        """Test high tier determination."""
        assert router._determine_tier(200.0) == "high"
        assert router._determine_tier(500.0) == "high"

    def test_tier_specific_thresholds(self):
        """Test tier-specific threshold overrides."""
        options = ComplexityRouterOptions(
            tiers=[
                ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"], max_score=30.0),
                ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"], min_score=30.1, max_score=100.0),
                ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"], min_score=100.1),
            ],
            backend_id="google",
        )
        context = Mock(spec=RouterContext)
        context.router_id = "test"
        context.is_backend_healthy = Mock(return_value=True)
        context.metrics_recorder = Mock()
        context.metrics_recorder.return_value.record_decision = Mock()
        
        router = ComplexityRouter(options=options, context=context)
        
        assert router._determine_tier(25.0) == "low"
        assert router._determine_tier(50.0) == "medium"
        assert router._determine_tier(150.0) == "high"


class TestModelSelection:
    """Test model selection logic."""

    def test_select_model_for_tier(self, router):
        """Test selection of model for tier."""
        model = router._select_model_for_tier("low")
        assert model == "gemini-2.0-flash-lite"

    def test_select_first_model_for_tier(self):
        """Test selection of first model in tier."""
        options = ComplexityRouterOptions(
            tiers=[
                ComplexityTierConfig(tier="low", models=["model-unavailable", "model-available"]),
                ComplexityTierConfig(tier="medium", models=["backend-medium"]),
                ComplexityTierConfig(tier="high", models=["backend-high"]),
            ],
            backend_id="google",
        )
        context = Mock(spec=RouterContext)
        context.router_id = "test"
        context.is_backend_healthy = Mock(return_value=True)
        context.metrics_recorder = Mock()
        context.metrics_recorder.return_value.record_decision = Mock()
        
        router = ComplexityRouter(options=options, context=context)
        
        model = router._select_model_for_tier("low")
        assert model == "model-unavailable"  # Returns first model regardless of availability

    def test_no_model_for_tier_returns_none(self):
        """Test that no model for tier returns None."""
        options = ComplexityRouterOptions(
            tiers=[
                ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
                ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
                ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"]),
            ],
            backend_id="google",
        )
        context = Mock(spec=RouterContext)
        context.router_id = "test"
        context.is_backend_healthy = Mock(return_value=True)
        context.metrics_recorder = Mock()
        context.metrics_recorder.return_value.record_decision = Mock()
        
        router = ComplexityRouter(options=options, context=context)
        
        # Test with a tier that doesn't exist
        model = router._select_model_for_tier("nonexistent")
        assert model is None


class TestRoutingLogic:
    """Test main routing logic."""

    @pytest.mark.anyio
    async def test_explicit_complexity_override(self, router):
        """Test explicit complexity metadata override."""
        request = GenerateRequest(
            prompt="This is a very long prompt that would normally score high",
            metadata={"complexity": "low"}
        )
        
        backend_id = await router.route(request)
        assert backend_id == "google"
        assert request.parameters["model"] == "gemini-2.0-flash-lite"
        
        # Verify metrics recording
        router._context.metrics_recorder.return_value.record_decision.assert_called_once()
        call_args = router._context.metrics_recorder.return_value.record_decision.call_args
        assert call_args[1]["reason"] == "explicit_complexity"
        assert call_args[1]["extra"]["complexity"] == "low"
        assert call_args[1]["extra"]["model"] == "gemini-2.0-flash-lite"

    @pytest.mark.anyio
    async def test_score_based_routing(self, router):
        """Test routing based on calculated score."""
        request = GenerateRequest(prompt="Hello")  # Low complexity
        
        backend_id = await router.route(request)
        assert backend_id == "google"
        assert request.parameters["model"] == "gemini-2.0-flash-lite"
        
        # Verify metrics recording
        call_args = router._context.metrics_recorder.return_value.record_decision.call_args
        assert call_args[1]["reason"] == "complexity_score"
        assert call_args[1]["extra"]["tier"] == "low"
        assert call_args[1]["extra"]["model"] == "gemini-2.0-flash-lite"

    @pytest.mark.anyio
    async def test_fallback_without_model(self):
        """Test fallback when no model is available for tier."""
        options = ComplexityRouterOptions(
            tiers=[
                ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
                ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
                ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"]),
            ],
            backend_id="google",
        )
        context = Mock(spec=RouterContext)
        context.router_id = "test"
        context.is_backend_healthy = Mock(return_value=True)
        context.metrics_recorder = Mock()
        context.metrics_recorder.return_value.record_decision = Mock()
        
        router = ComplexityRouter(options=options, context=context)
        
        # Mock the _select_model_for_tier to return None
        router._select_model_for_tier = Mock(return_value=None)
        
        request = GenerateRequest(prompt="Hello")
        backend_id = await router.route(request)
        assert backend_id == "google"
        assert "model" not in request.parameters  # No model set
        
        # Verify metrics recording
        call_args = router._context.metrics_recorder.return_value.record_decision.call_args
        assert call_args[1]["reason"] == "fallback"

    @pytest.mark.anyio
    async def test_honor_explicit_complexity_disabled(self):
        """Test that explicit complexity is ignored when disabled."""
        options = ComplexityRouterOptions(
            tiers=[
                ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
                ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
                ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"]),
            ],
            backend_id="google",
            honor_explicit_complexity=False,
        )
        context = Mock(spec=RouterContext)
        context.router_id = "test"
        context.is_backend_healthy = Mock(return_value=True)
        context.metrics_recorder = Mock()
        context.metrics_recorder.return_value.record_decision = Mock()
        
        router = ComplexityRouter(options=options, context=context)
        
        request = GenerateRequest(
            prompt="Hello",
            metadata={"complexity": "high"}  # Should be ignored
        )
        
        backend_id = await router.route(request)
        assert backend_id == "google"
        assert request.parameters["model"] == "gemini-2.0-flash-lite"  # Should route based on score, not metadata


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_missing_tiers_validation(self):
        """Test validation fails with missing tiers."""
        with pytest.raises(ValueError, match="requires all tiers"):
            ComplexityRouterOptions(
                tiers=[
                    ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
                    ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
                    # Missing high tier
                ],
                backend_id="google",
            )

    def test_invalid_thresholds_validation(self):
        """Test validation fails with invalid thresholds."""
        with pytest.raises(ValueError, match="low_threshold must be less than high_threshold"):
            ComplexityRouterOptions(
                tiers=[
                    ComplexityTierConfig(tier="low", models=["gemini-2.0-flash-lite"]),
                    ComplexityTierConfig(tier="medium", models=["gemini-2.0-flash"]),
                    ComplexityTierConfig(tier="high", models=["gemini-2.5-flash"]),
                ],
                low_threshold=200.0,
                high_threshold=50.0,  # Invalid: less than low_threshold
                backend_id="google",
            )

    def test_empty_tiers_validation(self):
        """Test validation fails with empty tiers."""
        with pytest.raises(ValueError, match="List should have at least 1 item"):
            ComplexityRouterOptions(tiers=[])


class TestFactoryFunction:
    """Test the factory function."""

    @pytest.mark.anyio
    async def test_build_complexity_router_with_dict_config(self):
        """Test building router with dictionary config."""
        config = {
            "tiers": [
                {"tier": "low", "models": ["gemini-2.0-flash-lite"]},
                {"tier": "medium", "models": ["gemini-2.0-flash"]},
                {"tier": "high", "models": ["gemini-2.5-flash"]},
            ],
            "low_threshold": 50.0,
            "high_threshold": 200.0,
            "backend_id": "google",
        }
        
        router = await build_complexity_router(config=config)
        assert isinstance(router, ComplexityRouter)

    @pytest.mark.anyio
    async def test_build_complexity_router_with_router_settings(self):
        """Test building router with RouterSettings config."""
        from accuralai_core.config.schema import RouterSettings
        
        config = RouterSettings(
            plugin="complexity",
            options={
                "tiers": [
                    {"tier": "low", "models": ["gemini-2.0-flash-lite"]},
                    {"tier": "medium", "models": ["gemini-2.0-flash"]},
                    {"tier": "high", "models": ["gemini-2.5-flash"]},
                ],
            },
            default_backend="google",
        )
        
        router = await build_complexity_router(config=config)
        assert isinstance(router, ComplexityRouter)
        assert router._options.backend_id == "google"
