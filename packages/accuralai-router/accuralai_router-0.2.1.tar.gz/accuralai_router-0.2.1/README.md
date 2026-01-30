# accuralai-router

`accuralai-router` provides pluggable routing strategies for the AccuralAI orchestration core. Routers map canonicalized requests to backend identifiers using deterministic policies, weighted load balancing, failover rules, metadata-aware predicates, or complexity-based tiering.

## Features

- Async routers that satisfy the `Router` protocol from `accuralai-core`.
- Direct routing honoring request hints or configured defaults.
- Weighted distribution with deterministic seeding and optional per-backend capacity limits.
- Health-aware failover that cycles through fallback backends.
- Rules engine that matches tags, metadata, or parameter values.
- **Complexity-based routing** that intelligently routes simple tasks to efficient models and complex tasks to powerful models.

Install alongside the core orchestrator:

```bash
pip install accuralai-core accuralai-router
```

## Complexity Router

The complexity router analyzes request characteristics to automatically route tasks to appropriate model tiers, optimizing cost and performance.

### Scoring Factors

The router calculates a complexity score using configurable weights:

- **Token count**: Base complexity from prompt + system_prompt + history length
- **History depth**: Additional points per conversation turn (default: 2.0 per turn)
- **Tool presence**: Flat bonus for requests with tools defined (default: 10.0)
- **Parameter complexity**: Advanced generation parameters like extreme temperatures, top_k, custom params (default: 5.0 weight)

### Tier Assignment

Requests are routed to three tiers based on score thresholds:

- **Low tier** (`< 50`): Simple tasks → efficient models (e.g., `gemini-2.0-flash-lite`)
- **Medium tier** (`50-199`): Moderate tasks → balanced models (e.g., `gemini-2.0-flash`)
- **High tier** (`≥ 200`): Complex tasks → powerful models (e.g., `gemini-2.5-flash`)

### Configuration Example

```toml
[router]
plugin = "complexity"
[router.options]
low_threshold = 50.0
high_threshold = 200.0
honor_explicit_complexity = true
backend_id = "google"

[router.options.scoring]
token_weight = 1.0
history_weight = 2.0
tool_weight = 10.0
parameter_complexity_weight = 5.0

[[router.options.tiers]]
tier = "low"
models = ["gemini-2.0-flash-lite"]

[[router.options.tiers]]
tier = "medium"
models = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

[[router.options.tiers]]
tier = "high"
models = ["gemini-2.5-flash", "gemini-2.0-flash"]

# Single backend configuration
[backends.google]
plugin = "google"
[backends.google.options]
model = "gemini-2.5-flash"  # Default model, overridden by router
```

### Explicit Complexity Override

You can override automatic scoring by setting explicit complexity in request metadata:

```python
request = GenerateRequest(
    prompt="Complex task that should use powerful model",
    metadata={"complexity": "high"}  # Forces high-tier routing
)
```

### Tuning Complexity Scoring

Adjust scoring weights based on your use case:

- **Higher `token_weight`**: Emphasize prompt length
- **Higher `history_weight`**: Penalize long conversations more
- **Higher `tool_weight`**: Treat tool usage as more complex
- **Higher `parameter_complexity_weight`**: Weight advanced generation parameters more

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e packages/accuralai-core[dev]
pip install -e packages/accuralai-router[dev]
pytest packages/accuralai-router/tests -q
```

Routers register entry points under `accuralai_core.routers` so `accuralai-core` can discover them automatically.
