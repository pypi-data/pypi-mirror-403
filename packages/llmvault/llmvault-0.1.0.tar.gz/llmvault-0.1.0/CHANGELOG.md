# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation: getting-started guide, attack catalog, custom attacks/evaluators guides, CI/CD guide
- Example scripts: basic usage, custom attacks, custom evaluators, batch testing, CI integration
- CONTRIBUTING.md with development setup and contribution guidelines
- GitHub Actions CI workflow (Python 3.10-3.13 matrix)
- GitHub issue and PR templates

## [0.1.0] - 2025-01-24

### Added
- Core architecture: async providers, Pydantic config, token bucket rate limiter
- 48 built-in attack templates across 6 categories (direct injection, indirect injection, jailbreak, role play, encoding, context overflow)
- 12 programmatic attack generators (base64, rot13, hex, leetspeak, unicode, padding, repetition, multi-turn, document flood, reverse text, markdown inject, comment inject)
- Async test runner with parallel execution (asyncio.Semaphore) and exponential backoff retry
- Heuristic response evaluator (20+ refusal patterns, system prompt leak detection, identity shift detection, compliance markers)
- CLI with Rich terminal output (progress bars, severity-colored tables, category/severity breakdowns)
- HTML report generation (self-contained, dark theme, Jinja2 template)
- JSON report output for machine consumption
- SARIF v2.1.0 report for GitHub Security tab integration
- YAML configuration file support (auto-discovery walking up from CWD, `$ENV_VAR` resolution)
- System prompt support (`--system-prompt`, `--system-prompt-file`)
- Custom attack patterns via YAML (`--patterns`, `--no-builtins`)
- Custom evaluator plugins via importlib (`--evaluator module:attr`)
- Configurable exit codes (`--fail-on` severity threshold)
- Output format auto-detection from file extension
- Provider support: OpenAI, Anthropic, DeepSeek, Kimi, Groq, Together, Mistral, Ollama
- 285 unit tests with comprehensive mocking
