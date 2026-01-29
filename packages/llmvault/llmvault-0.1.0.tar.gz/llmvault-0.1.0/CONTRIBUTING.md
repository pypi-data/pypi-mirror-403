# Contributing to LLMVault

## Development Setup

```bash
# Clone the repo
git clone https://github.com/sharkfabri/LLMVault.git
cd llmvault

# Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running Checks

Run these locally before pushing:

```bash
# Unit tests
pytest

# Lint
ruff check src/

# Format check
ruff format --check src/ tests/

# Type check
mypy src/
```

All checks run automatically in CI on push and PRs.

## Code Style

- Python 3.10+ (use `X | Y` union syntax, not `Optional[X]`)
- Line length: 100 characters
- Linter: ruff (rules: E, F, W, I, N, UP, B, A, SIM)
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Docstrings: Google style
- No `print()` in library code (use `logging`)

## Project Layout

```
src/llmvault/
├── core/         # Config, YAML loading
├── providers/    # LLM provider implementations
├── attacks/      # Templates, engine, loader
├── runner/       # Test execution, evaluator, rate limiter
├── reporters/    # Output formats (CLI, HTML, JSON, SARIF)
└── cli/          # Typer CLI app
```

## Adding Attack Templates

1. Open `src/llmvault/attacks/templates.py`
2. Add your template to the appropriate category section:

```python
AttackTemplate(
    name="category-descriptive-name",
    category=AttackCategory.DIRECT_INJECTION,
    severity=Severity.HIGH,
    description="Brief description of what this attack does.",
    prompt_template="Your prompt with {action} variable substitution",
    intent="What a successful attack would demonstrate.",
    variables={"action": ACTIONS},
)
```

3. Add it to the appropriate category list (e.g., `DIRECT_TEMPLATES`)
4. Verify it's included via `ALL_TEMPLATES` at the bottom of the file
5. Run `pytest tests/unit/test_attack_engine.py` to verify

Variable pools (`ACTIONS`, `ROLES`, `TOPICS`, etc.) are defined at the top of the file.

## Adding a Generator

Generators produce attack prompts programmatically (e.g., encoding, obfuscation).

1. Add your generator function to `src/llmvault/attacks/engine.py`:

```python
def _my_generator(action: str) -> str:
    """Brief description."""
    # Transform the action into an attack prompt
    return f"Generated prompt based on: {action}"
```

2. Register it in `_GENERATORS`:

```python
_GENERATORS: dict[str, Callable[[str], str]] = {
    # ... existing generators ...
    "my_generator": _my_generator,
}
```

3. `VALID_GENERATORS` updates automatically from `_GENERATORS.keys()`
4. Run `pytest tests/unit/test_attack_engine.py`

## Adding a Provider

1. Create `src/llmvault/providers/my_provider.py`:

```python
from llmvault.providers.base import LLMProvider

class MyProvider(LLMProvider):
    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        # Call your API here
        ...
```

2. Register in `src/llmvault/providers/registry.py`:

```python
if provider == "my_provider":
    from llmvault.providers.my_provider import MyProvider
    return MyProvider(model=config.model, api_key=config.api_key)
```

3. Add prefix mapping in `src/llmvault/core/config.py`:

```python
PROVIDER_MAP: dict[str, str] = {
    # ... existing mappings ...
    "myprefix-": "my_provider",
}
```

4. Add optional dependency in `pyproject.toml`:

```toml
[project.optional-dependencies]
my_provider = ["my-sdk>=1.0"]
```

5. Write tests in `tests/unit/test_providers.py`

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Implement your changes
4. Run all checks locally (pytest, ruff, mypy)
5. Submit a PR against `main`
6. CI runs automatically and must pass
7. Address review feedback

Keep PRs focused on a single change. If you're adding a new feature, include tests.
