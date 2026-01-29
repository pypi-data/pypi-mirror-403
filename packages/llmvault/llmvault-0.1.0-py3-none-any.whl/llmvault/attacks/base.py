"""Base attack models for LLM security testing."""

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity level of an attack pattern."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackCategory(str, Enum):
    """Categories of prompt injection attacks."""

    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    JAILBREAK = "jailbreak"
    ROLE_PLAY = "role_play"
    ENCODING = "encoding"
    CONTEXT_OVERFLOW = "context_overflow"


class Attack(BaseModel):
    """A single attack pattern for testing LLM security."""

    name: str
    category: AttackCategory
    severity: Severity = Severity.MEDIUM
    description: str = ""
    prompt: str
    intent: str = Field(
        default="",
        description="The malicious intent of this attack, used for evaluating responses.",
    )
    system_prompt: str | None = None


class AttackResult(BaseModel):
    """Result of a single attack execution."""

    attack: Attack
    response: str
    is_vulnerable: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""
