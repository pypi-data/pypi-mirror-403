"""Custom attack pattern loader from YAML files."""

from pathlib import Path

import yaml

from llmvault.attacks.base import AttackCategory, Severity
from llmvault.attacks.engine import VALID_GENERATORS
from llmvault.attacks.templates import AttackTemplate


def load_patterns(path: Path) -> list[AttackTemplate]:
    """Load custom attack patterns from a YAML file or directory.

    If path is a file, load it directly.
    If path is a directory, load all *.yaml files in it.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If any pattern file is invalid.
    """
    if not path.exists():
        msg = f"Patterns path not found: {path}"
        raise FileNotFoundError(msg)

    if path.is_dir():
        templates: list[AttackTemplate] = []
        yaml_files = sorted(path.glob("*.yaml"))
        if not yaml_files:
            msg = f"No .yaml files found in directory: {path}"
            raise ValueError(msg)
        for f in yaml_files:
            templates.extend(_load_single_file(f))
        return templates

    return _load_single_file(path)


def _load_single_file(path: Path) -> list[AttackTemplate]:
    """Load patterns from a single YAML file."""
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        msg = f"Invalid YAML in {path}: {e}"
        raise ValueError(msg) from e

    if data is None:
        return []

    if not isinstance(data, dict):
        msg = f"Pattern file must contain a YAML mapping, got {type(data).__name__}"
        raise ValueError(msg)

    global_vars = data.get("variables", {})
    if not isinstance(global_vars, dict):
        msg = "Top-level 'variables' must be a mapping"
        raise ValueError(msg)

    raw_templates = data.get("templates", [])
    if not isinstance(raw_templates, list):
        msg = "'templates' must be a list"
        raise ValueError(msg)

    results: list[AttackTemplate] = []
    for i, entry in enumerate(raw_templates):
        template = _validate_template_entry(entry, global_vars, index=i)
        results.append(template)

    return results


def resolve_variable_refs(
    template_vars: dict[str, object],
    global_vars: dict[str, object],
) -> dict[str, list[str]]:
    """Resolve $ref variable references from template-level to global variables.

    Template variables can either be:
    - A list of strings (inline values)
    - A string starting with '$' (reference to a global variable)
    """
    resolved: dict[str, list[str]] = {}
    for key, value in template_vars.items():
        if isinstance(value, str) and value.startswith("$"):
            ref_name = value[1:]
            if ref_name not in global_vars:
                msg = f"Variable reference '${ref_name}' not found in global variables"
                raise ValueError(msg)
            ref_value = global_vars[ref_name]
            if not isinstance(ref_value, list):
                msg = f"Global variable '{ref_name}' must be a list, got {type(ref_value).__name__}"
                raise ValueError(msg)
            resolved[key] = [str(v) for v in ref_value]
        elif isinstance(value, list):
            resolved[key] = [str(v) for v in value]
        else:
            msg = f"Variable '{key}' must be a list or a $reference, got {type(value).__name__}"
            raise ValueError(msg)
    return resolved


def _validate_template_entry(
    entry: object,
    global_vars: dict[str, object],
    index: int,
) -> AttackTemplate:
    """Validate and convert a raw template entry to an AttackTemplate."""
    if not isinstance(entry, dict):
        msg = f"Template at index {index} must be a mapping"
        raise ValueError(msg)

    # Required fields
    for field in ("name", "category", "prompt_template", "intent"):
        if field not in entry:
            msg = f"Template at index {index} missing required field '{field}'"
            raise ValueError(msg)

    # Validate category
    category_str = entry["category"]
    try:
        category = AttackCategory(category_str)
    except ValueError:
        valid = [c.value for c in AttackCategory]
        msg = f"Template '{entry['name']}': invalid category '{category_str}'. Valid: {valid}"
        raise ValueError(msg) from None

    # Validate severity
    severity_str = entry.get("severity", "medium")
    try:
        severity_val = Severity(severity_str)
    except ValueError:
        valid = [s.value for s in Severity]
        msg = f"Template '{entry['name']}': invalid severity '{severity_str}'. Valid: {valid}"
        raise ValueError(msg) from None

    # Validate generator
    generator = entry.get("generator")
    if generator is not None and generator not in VALID_GENERATORS:
        msg = (
            f"Template '{entry['name']}': invalid generator '{generator}'. "
            f"Valid: {sorted(VALID_GENERATORS)}"
        )
        raise ValueError(msg)

    # Resolve variables
    raw_vars = entry.get("variables", {})
    if not isinstance(raw_vars, dict):
        msg = f"Template '{entry['name']}': 'variables' must be a mapping"
        raise ValueError(msg)
    variables = resolve_variable_refs(raw_vars, global_vars)

    return AttackTemplate(
        name=entry["name"],
        category=category,
        severity=severity_val,
        description=entry.get("description", ""),
        prompt_template=entry["prompt_template"],
        intent=entry["intent"],
        variables=variables,
        generator=generator,
    )
