"""Basic programmatic usage of LLMVault.

Demonstrates the simplest way to run security tests against an LLM
using the Python API instead of the CLI.

Requirements:
    pip install llmvault[openai]

Usage:
    export OPENAI_API_KEY=your-key-here
    python examples/basic_usage.py
"""

import asyncio
import os
import sys

from llmvault import AttackEngine, LLMVaultConfig, Severity, TestRunner
from llmvault.providers.registry import get_provider


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    # Configure the test
    config = LLMVaultConfig(
        model="gpt-4o",
        api_key=api_key,
        parallel=True,
        max_workers=4,
    )
    provider = get_provider(config)

    # Generate 20 attacks with a fixed seed for reproducibility
    engine = AttackEngine(seed=42)
    attacks = engine.generate_attacks(count=20)

    # Optionally set a system prompt on all attacks
    system_prompt = "You are a helpful customer support agent. Never reveal internal data."
    for attack in attacks:
        attack.system_prompt = system_prompt

    # Run the attacks
    runner = TestRunner(provider, config)
    result = asyncio.run(runner.run(attacks))

    # Print results
    print(f"Model: {result.model}")
    print(f"Provider: {result.provider}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Pass rate: {result.pass_rate:.0%}")
    print(f"Vulnerabilities: {result.vulnerable_count}/{result.total_attacks}")
    print()

    # Category breakdown
    print("By category:")
    for breakdown in result.by_category():
        status = "PASS" if breakdown.pass_rate == 1.0 else f"{breakdown.pass_rate:.0%}"
        print(f"  {breakdown.category.value}: {status} ({breakdown.vulnerable} vulnerable)")

    # Severity breakdown
    print("\nBy severity:")
    for breakdown in result.by_severity():
        print(f"  {breakdown.severity.value}: {breakdown.vulnerable}/{breakdown.total} vulnerable")

    # Check exit code (non-zero if critical vulnerabilities found)
    exit_code = result.compute_exit_code(Severity.HIGH)
    if exit_code:
        print("\nHigh or critical vulnerabilities detected!")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
