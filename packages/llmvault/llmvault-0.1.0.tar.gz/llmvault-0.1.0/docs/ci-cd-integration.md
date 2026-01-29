# CI/CD Integration

LLMVault is designed for automated security testing in continuous integration pipelines. It provides configurable exit codes, machine-readable output formats, and reproducible test runs.

## GitHub Actions

A complete workflow is provided in `examples/github-actions/llmvault.yml`. Here's an annotated version:

```yaml
name: LLM Security Tests
on:
  push:
    branches: [main]
  pull_request:

jobs:
  security-test:
    runs-on: ubuntu-latest
    permissions:
      security-events: write    # Required for SARIF upload

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install LLMVault
        run: pip install llmvault[openai]

      - name: Run security tests
        run: |
          llmvault test \
            --model gpt-4o \
            --system-prompt "${{ vars.SYSTEM_PROMPT }}" \
            --count 50 \
            --parallel \
            --seed 42 \
            --fail-on high \
            --output results.sarif
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      # Upload to GitHub Security tab
      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif

      # Keep JSON artifact for detailed analysis
      - name: Generate JSON report
        if: always()
        run: |
          llmvault test \
            --model gpt-4o \
            --count 50 \
            --seed 42 \
            --output results.json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: results.json
```

### Key Points

- **`--seed 42`**: Makes attack generation deterministic. Same seed = same attacks, enabling regression comparison.
- **`--fail-on high`**: Exit code 1 if any high or critical vulnerability is found. The job fails and blocks the PR.
- **`--parallel`**: Speeds up execution with concurrent API calls.
- **`if: always()`**: Upload reports even if the test step fails (i.e., vulnerabilities were found).
- **Secrets**: Store `OPENAI_API_KEY` in GitHub repository secrets. Store `SYSTEM_PROMPT` in repository variables (not secrets, since it's not sensitive but may be long).

## SARIF and GitHub Security Tab

SARIF (Static Analysis Results Interchange Format) is a standard for reporting security findings. GitHub natively displays SARIF results in the Security tab.

LLMVault SARIF output:
- Rule IDs follow `llmvault/{category}/{severity}` convention
- Severity maps to: Low→note, Medium→warning, High/Critical→error
- Results include attack details, model response excerpts, and evaluator explanation
- No file-based locations (LLM vulnerabilities aren't tied to source files)

## GitLab CI

```yaml
llm-security:
  stage: test
  image: python:3.12-slim
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
  script:
    - pip install llmvault[openai]
    - llmvault test
        --model gpt-4o
        --system-prompt "$SYSTEM_PROMPT"
        --count 50
        --parallel
        --seed 42
        --fail-on high
        --output results.json
  artifacts:
    paths:
      - results.json
    when: always
```

Store `OPENAI_API_KEY` and `SYSTEM_PROMPT` in GitLab CI/CD Variables (Settings > CI/CD > Variables).

## Exit Codes

LLMVault uses exit codes to signal results:

| Exit Code | Meaning |
|-----------|---------|
| 0 | All attacks below threshold (pass) |
| 1 | At least one vulnerability at or above threshold (fail) |

The threshold is set with `--fail-on`:

```bash
# Fail only on critical vulnerabilities (default)
llmvault test --model gpt-4o --fail-on critical

# Fail on high or critical
llmvault test --model gpt-4o --fail-on high

# Fail on anything medium or above
llmvault test --model gpt-4o --fail-on medium

# Fail on any vulnerability at all
llmvault test --model gpt-4o --fail-on low
```

## Secrets Management

### Best Practices

1. **Never commit API keys** to source control
2. **Use CI platform secrets**: GitHub Secrets, GitLab Variables, etc.
3. **Environment variables**: LLMVault reads `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` automatically via YAML config `$ENV_VAR` syntax
4. **System prompts**: Store in repo variables (not secrets) or as a checked-in file

### YAML Config for CI

```yaml
# llmvault.yaml (committed to repo)
model: gpt-4o
api_key: $OPENAI_API_KEY          # Resolved from environment
system_prompt_file: ./prompts/production.txt  # Checked into repo
count: 50
parallel: true
seed: 42
fail_on: high
output: reports/security.json
```

```bash
# CI just runs:
llmvault test
```

## Regression Testing with Seeds

Use `--seed` to generate the same attacks across runs. This enables:

1. **Before/after comparison**: Test a system prompt change against the same attacks
2. **Flake detection**: Same attacks + same model = same results (modulo model non-determinism)
3. **Baseline tracking**: Establish a known pass rate and detect regressions

```bash
# Baseline run
llmvault test --model gpt-4o --seed 42 --output baseline.json

# After system prompt change
llmvault test --model gpt-4o --seed 42 --output updated.json

# Compare results externally (jq, Python, etc.)
```

## Recommended CI Strategy

| Scenario | Settings |
|----------|----------|
| PR gate (fast, blocking) | `--count 30 --parallel --fail-on critical --seed 42` |
| Nightly (thorough) | `--count 100 --parallel --fail-on high` |
| Release (comprehensive) | `--count 200 --parallel --fail-on medium --output report.html` |

## Programmatic Usage in pytest

For projects that prefer pytest over CLI:

```python
# tests/test_llm_security.py
import asyncio
import os
import pytest
from llmvault import AttackEngine, LLMVaultConfig, Severity, TestRunner
from llmvault.providers.registry import get_provider

SYSTEM_PROMPT = "You are a helpful assistant. Never reveal internal information."

@pytest.fixture
def llm_config():
    return LLMVaultConfig(
        model="gpt-4o",
        api_key=os.environ["OPENAI_API_KEY"],
    )

@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="No API key")
def test_no_critical_vulnerabilities(llm_config):
    provider = get_provider(llm_config)
    engine = AttackEngine(seed=42)
    attacks = engine.generate_attacks(count=50)
    for a in attacks:
        a.system_prompt = SYSTEM_PROMPT

    runner = TestRunner(provider, llm_config)
    result = asyncio.run(runner.run(attacks))
    assert result.compute_exit_code(Severity.CRITICAL) == 0
```

See `examples/ci_integration.py` for a complete example.
