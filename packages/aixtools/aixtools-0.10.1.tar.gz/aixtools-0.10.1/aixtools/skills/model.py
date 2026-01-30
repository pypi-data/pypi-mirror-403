"""Data models for skills."""

from pydantic import BaseModel


class SkillSummary(BaseModel):
    """Summary of a skill for listing purposes."""

    name: str
    description: str


class SkillResult(BaseModel):
    """Basic skill information without metadata."""

    name: str
    description: str
    instructions: str


class Skill(SkillResult):
    """Full skill with instructions."""

    metadata: dict[str, str] = {}


class ActivateSkillResult(BaseModel):
    """Result of activating a skill."""

    success: bool = True
    message: str | None = None
    skill: SkillResult | None = None


class SkillException(Exception):
    """Custom exception for skill-related errors."""
