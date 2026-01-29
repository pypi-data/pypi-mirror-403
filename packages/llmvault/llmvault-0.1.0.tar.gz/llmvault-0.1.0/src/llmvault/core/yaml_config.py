"""YAML configuration file discovery, loading, and merging for LLMVault."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class YAMLConfigFile(BaseModel):
    """Parsed YAML configuration file model."""

    model: str | None = None
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    count: int | None = None
    categories: list[str] | None = None
    severity: str | None = None
    parallel: bool | None = None
    max_workers: int | None = None
    seed: int | None = None
    output: str | None = None
    rpm: int | None = None
    patterns: str | None = None
    no_builtins: bool | None = None
    system_prompt: str | None = None
    system_prompt_file: str | None = None
    fail_on: str | None = None
    evaluator: str | None = None
    format: str | None = None

    @field_validator("api_key", "base_url", mode="before")
    @classmethod
    def resolve_env_vars(cls, v: object) -> object:
        """Resolve $ENV_VAR references in string fields."""
        if isinstance(v, str):
            return resolve_env_reference(v)
        return v


def resolve_env_reference(value: str) -> str:
    """Resolve $ENV_VAR references to environment variable values.

    If the value starts with '$', look up the rest as an environment variable.
    Returns the original string if not an env reference or if the variable is not set.
    """
    if value.startswith("$") and len(value) > 1:
        var_name = value[1:]
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
    return value


_CONFIG_FILENAMES = ("llmvault.yaml", ".llmvault.yaml")


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Search for a config file from start_dir upward, stopping at home dir.

    Looks for 'llmvault.yaml' or '.llmvault.yaml' in each directory.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    home = Path.home()
    current = start_dir.resolve()

    while True:
        for name in _CONFIG_FILENAMES:
            candidate = current / name
            if candidate.is_file():
                return candidate

        parent = current.parent
        if parent == current:
            break
        if current == home:
            break
        current = parent

    return None


def load_yaml_config(path: Path) -> YAMLConfigFile:
    """Load and validate a YAML configuration file.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the YAML is invalid or cannot be parsed.
    """
    if not path.exists():
        msg = f"Config file not found: {path}"
        raise FileNotFoundError(msg)

    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        msg = f"Invalid YAML in {path}: {e}"
        raise ValueError(msg) from e

    if data is None:
        return YAMLConfigFile()

    if not isinstance(data, dict):
        msg = f"Config file must contain a YAML mapping, got {type(data).__name__}"
        raise ValueError(msg)

    return YAMLConfigFile(**data)
