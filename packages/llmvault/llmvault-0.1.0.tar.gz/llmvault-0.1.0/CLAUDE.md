# CLAUDE.md - Project Context for LLMVault

## What is this project?

LLMVault is a security testing toolkit for LLM prompt injection vulnerabilities. It tests models against known attack patterns and generates vulnerability reports. Local-first, multi-provider, Python 3.10+.

## Project Structure

```
src/llmvault/
├── __init__.py              # Package root, version, public exports
├── core/
│   ├── config.py            # LLMVaultConfig, RateLimitConfig, provider auto-detection
│   └── yaml_config.py      # YAML config discovery, loading, env var resolution
├── providers/
│   ├── base.py              # LLMProvider abstract base class
│   ├── registry.py          # get_provider() factory function
│   ├── openai_compat.py     # OpenAI-compatible provider (OpenAI, DeepSeek, Groq, etc.)
│   ├── anthropic_provider.py # Anthropic native API
│   └── ollama_provider.py   # Local Ollama inference
├── attacks/
│   ├── base.py              # Attack, AttackResult, AttackCategory, Severity models
│   ├── templates.py         # 48 AttackTemplate definitions across 6 categories
│   ├── engine.py            # AttackEngine: generates concrete Attacks from templates (12 generators)
│   └── loader.py            # Custom YAML pattern loading and validation
├── runner/
│   ├── __init__.py          # Public exports (TestRunner, TestSuiteResult, Evaluator, etc.)
│   ├── rate_limiter.py      # Token bucket async rate limiter
│   ├── evaluator.py         # Heuristic response evaluator (refusal/leak/compliance detection)
│   ├── evaluator_loader.py  # Custom evaluator plugin loading (module:attr spec)
│   ├── models.py            # TestSuiteResult, CategoryBreakdown, SeverityBreakdown
│   └── engine.py            # TestRunner: async orchestration with retry, concurrency
├── reporters/
│   ├── __init__.py          # Exports CLIReporter, HTMLReporter, JSONReporter, SARIFReporter
│   ├── cli_reporter.py     # Rich terminal output (progress, tables, summary)
│   ├── html_reporter.py    # Jinja2-based HTML report generation
│   ├── json_reporter.py    # Machine-readable JSON report generation
│   ├── sarif_reporter.py   # SARIF v2.1.0 report for GitHub Security/CI tools
│   └── templates/
│       └── report.html      # Self-contained HTML report template (dark theme)
└── cli/
    └── main.py              # Typer CLI app (test, attacks commands, YAML config merge)

tests/
├── unit/
│   ├── test_config.py       # Config and provider detection tests
│   ├── test_providers.py    # Provider registry and instantiation tests
│   ├── test_attack_engine.py # Attack engine, templates, generators, and generation tests
│   ├── test_rate_limiter.py # Token bucket rate limiter tests
│   ├── test_evaluator.py   # Evaluator heuristic detection tests
│   ├── test_runner.py      # Runner orchestration tests (mock provider)
│   ├── test_reporters.py   # CLI and HTML reporter tests
│   ├── test_cli.py         # CLI command tests (typer CliRunner)
│   ├── test_yaml_config.py # YAML config discovery, loading, merge tests
│   ├── test_pattern_loader.py # Custom pattern loader tests
│   ├── test_system_prompt.py # System prompt propagation tests
│   ├── test_json_reporter.py # JSON reporter tests
│   ├── test_sarif_reporter.py # SARIF reporter tests
│   └── test_evaluator_loader.py # Evaluator plugin loader tests
├── unit/fixtures/
│   └── custom_evaluator.py  # Test fixture evaluators for plugin tests
└── integration/             # Integration tests (requires API keys)
```

## Key Architecture Decisions

- **Optional LLM deps**: Core has no LLM SDK dependencies. Providers are installed via extras (`pip install llmvault[openai]`). Import errors at runtime give clear install instructions.
- **OpenAI-compatible pattern**: Most providers (DeepSeek, Groq, Together, Mistral, Kimi) use the same OpenAI chat completions API format. A single `OpenAICompatibleProvider` class handles all of them with configurable `base_url`.
- **Provider auto-detection**: Model name prefixes map to providers (e.g. `gpt-` -> openai, `claude-` -> anthropic). Users can always override explicitly.
- **Pydantic models**: All data structures use Pydantic v2 for validation.
- **Async-first**: Provider `send()` methods are all async.
- **Attack templates as Python data**: Built-in templates are defined in code for type safety. Custom templates can be loaded from YAML via `loader.py`. `AttackEngine` generates concrete `Attack` instances via `str.format_map()` variable substitution and programmatic generators (12 generators for encoding/overflow/smuggling attacks). Reproducible via `seed` parameter.
- **YAML configuration**: `yaml_config.py` discovers `llmvault.yaml` or `.llmvault.yaml` by walking up from CWD. Supports `$ENV_VAR` references for API keys. CLI args override YAML values override hardcoded defaults.
- **Custom patterns via YAML**: `loader.py` loads attack templates from YAML files or directories. Supports `$ref` variable references, validates category/severity/generator names. Merged with built-in templates (or used standalone with `--no-builtins`).
- **System prompt support**: `--system-prompt` or `--system-prompt-file` sets a system prompt on all generated attacks. Providers receive it via the `Attack.system_prompt` field.
- **Heuristic evaluator**: Response evaluation uses regex pattern matching (20+ refusal patterns, system prompt leak detection, identity shift, compliance markers). Priority order: empty → refusal → leak → identity shift → compliance → ambiguous. Conservative default: ambiguous = not vulnerable (false negatives over false positives).
- **Token bucket rate limiter**: Async-compatible (`asyncio.Lock`), starts full for burst, refills at steady rate. Simple enough for ≤4 concurrent workers.
- **Test runner never raises**: All errors become `AttackResult` with `is_vulnerable=False`. Retry with exponential backoff. Supports sequential and parallel (`asyncio.Semaphore`) execution.
- **CLI uses asyncio.run()**: TestRunner is async-first; CLI bridges sync/async with `asyncio.run()`. Progress callback (`on_progress`) is called per-attack for real-time feedback.
- **HTML reports are self-contained**: Single file, inline CSS, no external dependencies. Jinja2 template with `autoescape=True` for XSS safety.
- **Multiple output formats**: CLI auto-detects format from file extension (`.html`, `.json`, `.sarif`). Explicit `--format` flag overrides. All reporters share the same interface: `generate(result, output_path)`.
- **SARIF v2.1.0 without locations**: LLM vulnerabilities are not file-based, so SARIF results omit `locations` and use `properties` bag for metadata. Rule IDs follow `llmvault/{category}/{severity}` convention.
- **Configurable exit codes**: `compute_exit_code(fail_on)` method allows CI pipelines to set severity threshold. Default `exit_code` property remains for backward compat.
- **Evaluator plugins via importlib**: `load_evaluator("module:attr")` loads custom evaluators. Classes with `evaluate()` method are used directly; bare functions are wrapped in `EvaluatorPlugin` adapter. No plugin framework dependency.

## Commands

```bash
# Run in the virtual environment
.venv/Scripts/activate       # Windows
source .venv/bin/activate    # Linux/Mac

# Development
pip install -e ".[dev]"      # Install with dev deps
pytest                       # Run tests (285 tests)
ruff check src/              # Lint
mypy src/                    # Type check
llmvault --help              # CLI

# With extras
pip install -e ".[openai]"   # Add OpenAI support
pip install -e ".[all]"      # Add all providers

# CLI usage
llmvault test --model gpt-4o --api-key $KEY               # Basic test
llmvault test --config llmvault.yaml                       # Use YAML config
llmvault test --model gpt-4o --system-prompt "You are a bot" # With system prompt
llmvault test --model gpt-4o --patterns ./custom/ --no-builtins  # Custom patterns only
llmvault test --model gpt-4o --output report.json              # JSON output
llmvault test --model gpt-4o --output report.sarif             # SARIF output
llmvault test --model gpt-4o --fail-on high                    # Exit 1 on high+ vulns
llmvault test --model gpt-4o --evaluator mymod:MyEval          # Custom evaluator
llmvault attacks                                           # List 48 templates
```

## Code Style

- Python 3.10+ (use `X | Y` union syntax, not `Optional[X]`)
- Line length: 100 chars
- Linter: ruff (E, F, W, I, N, UP, B, A, SIM rules)
- Type checker: mypy (strict mode)
- Formatter: ruff format
- Test framework: pytest + pytest-asyncio

## Implementation Status

### Completed
- **Task 1.1**: Project setup - pyproject.toml, provider architecture, config, CLI stub, tests
- **Task 1.2**: Attack engine - 24 templates (4 per category), AttackEngine with variable substitution and programmatic generators, Severity enum
- **Task 1.3**: Test runner - async TestRunner (sequential/parallel), token bucket RateLimiter, heuristic Evaluator, TestSuiteResult with category/severity breakdowns
- **Task 1.4**: CLI + reporting - Rich progress/summary (CLIReporter), HTML reports via Jinja2 (HTMLReporter), full CLI wiring with --count, --category, --severity, --parallel, --output, --seed, --rpm options
- **Task 2.1**: YAML configuration - `yaml_config.py` with file discovery (walk up from CWD), `$ENV_VAR` resolution, Pydantic model, CLI merge (CLI > YAML > defaults)
- **Task 2.2**: System prompt support - `--system-prompt` and `--system-prompt-file` CLI options, YAML support, propagation to all generated attacks
- **Task 2.3**: Custom attack patterns - `loader.py` YAML loader with `$ref` variable resolution, category/severity/generator validation, `--patterns` and `--no-builtins` CLI options
- **Task 2.4**: Advanced attacks - 24 new templates (payload splitting, token smuggling, gradual escalation, authority impersonation, refusal suppression, multi-language), 4 new generators (hex_encode, reverse_text, markdown_inject, comment_inject), expanded variable pools (SECRETS, AUTHORITIES, +4 ACTIONS, +4 TOPICS)

- **Task 3.1**: JSON reporter - `json_reporter.py` with `to_dict()` and `generate()`, machine-readable output
- **Task 3.2**: Enhanced exit codes - `compute_exit_code(fail_on)` method on TestSuiteResult, `--fail-on` CLI option
- **Task 3.3**: Custom evaluator plugins - `evaluator_loader.py` with `load_evaluator(spec)`, `EvaluatorPlugin` adapter, `--evaluator` CLI option
- **Task 3.4**: SARIF reporter - `sarif_reporter.py` with SARIF v2.1.0 output, rule deduplication, severity-to-level mapping
- **Task 3.5**: CLI format dispatch - auto-detect output format from extension, `--format` option, GitHub Actions workflow template

### Next Steps
- Phase 4: Documentation site, example gallery, GitHub polish

## Design Principles

1. **Local-first**: No cloud dependencies for core functionality, no telemetry
2. **Minimal deps**: Core only needs pydantic, rich, typer, jinja2, pyyaml, aiohttp
3. **Provider-agnostic**: Works with any LLM that has an API
4. **Smart evaluation**: Don't flag legitimate refusals as vulnerabilities - track attack intent
5. **Rate limiting**: Built-in, configurable per-provider defaults
6. **No over-engineering**: Simple implementations, no premature abstractions
