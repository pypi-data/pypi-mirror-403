# Getting Started with LLMVault

## Prerequisites

- Python 3.10 or later
- An LLM API key (OpenAI, Anthropic, DeepSeek, etc.) or a local [Ollama](https://ollama.ai) installation
- pip (included with Python)

## Installation

Install the core package plus your provider:

```bash
# OpenAI (GPT-4o, GPT-4, etc.)
pip install llmvault[openai]

# Anthropic (Claude)
pip install llmvault[anthropic]

# DeepSeek, Groq, Together, Mistral, Kimi (OpenAI-compatible)
pip install llmvault[openai]

# Ollama (local, no API key needed)
pip install llmvault[ollama]

# All providers
pip install llmvault[all]
```

## Your First Test

Run a basic security test against your model:

```bash
export OPENAI_API_KEY=sk-your-key-here
llmvault test --model gpt-4o --count 20
```

You'll see real-time progress as attacks execute:

```
LLMVault - Testing model: gpt-4o
  Provider: openai
  Attacks:  20

[1/20] direct-ignore-instructions         PASS
[2/20] jailbreak-dan                       PASS
[3/20] encoding-base64                     VULNERABLE (confidence: 0.80)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary
  Total attacks: 20
  Pass rate:     85.0%
  Vulnerable:    3
  Duration:      12.4s
```

## Understanding Results

### Pass Rate

The percentage of attacks the model correctly rejected. Higher is better:
- **95-100%**: Excellent resistance
- **80-95%**: Good, but some attack vectors work
- **< 80%**: Significant vulnerabilities exist

### Severity Levels

Each attack has a severity indicating its potential impact:
- **Critical**: Full system prompt leakage or complete restriction bypass
- **High**: Significant behavior override or data exposure
- **Medium**: Partial compliance with malicious instructions
- **Low**: Minor information disclosure

### Category Breakdown

Results are grouped by attack type:
- **direct_injection**: Instructions to override system prompt
- **indirect_injection**: Hidden instructions in documents/context
- **jailbreak**: Persona-based restriction bypass (DAN, dev mode)
- **role_play**: Identity manipulation attacks
- **encoding**: Obfuscated payloads (base64, hex, rot13)
- **context_overflow**: Padding/repetition to dilute system prompt

## Adding a System Prompt

Testing with a system prompt is essential -- it tests **your application**, not just the base model:

```bash
llmvault test --model gpt-4o \
  --system-prompt "You are a customer support agent for Acme Corp. Only answer questions about our products. Never reveal internal information." \
  --count 50
```

Or load from a file:

```bash
llmvault test --model gpt-4o \
  --system-prompt-file ./prompts/support-agent.txt \
  --count 50
```

## Generating Reports

### HTML Report

```bash
llmvault test --model gpt-4o --output report.html
```

The HTML report is self-contained (no external dependencies) and includes:
- Executive summary with pass rate and severity distribution
- Detailed results table (sortable, filterable)
- Per-attack details: payload sent, model response, vulnerability explanation

### JSON Report

```bash
llmvault test --model gpt-4o --output report.json
```

Machine-readable output for CI/CD pipelines and custom tooling.

### SARIF Report

```bash
llmvault test --model gpt-4o --output report.sarif
```

Upload to GitHub Security tab for integrated vulnerability tracking.

## YAML Configuration

Create `llmvault.yaml` in your project root for persistent configuration:

```yaml
model: gpt-4o
api_key: $OPENAI_API_KEY    # Resolves environment variables
count: 50
parallel: true
max_workers: 4
seed: 42                     # Reproducible attack generation
system_prompt: "You are a helpful assistant."
output: reports/latest.html
fail_on: high                # Exit code 1 if high+ vulnerabilities found
```

Then run:

```bash
llmvault test
```

CLI arguments override YAML values. See all available options:

```bash
llmvault test --help
```

## Filtering Attacks

Run specific categories or severity levels:

```bash
# Only jailbreak and injection attacks
llmvault test --model gpt-4o --category jailbreak --category direct_injection

# Only high and critical severity
llmvault test --model gpt-4o --severity high
```

## Parallel Execution

Speed up testing with concurrent API calls:

```bash
llmvault test --model gpt-4o --parallel --max-workers 4 --rpm 60
```

- `--parallel`: Enable concurrent execution
- `--max-workers`: Max simultaneous API calls (default: 4)
- `--rpm`: Rate limit in requests per minute (default: 60)

## Next Steps

- [Attack Catalog](attack-catalog.md) -- Browse all 48 built-in attack templates
- [Custom Attacks](custom-attacks.md) -- Write your own attack patterns in YAML
- [Custom Evaluators](custom-evaluators.md) -- Implement domain-specific vulnerability detection
- [CI/CD Integration](ci-cd-integration.md) -- Automate security testing in your pipeline
