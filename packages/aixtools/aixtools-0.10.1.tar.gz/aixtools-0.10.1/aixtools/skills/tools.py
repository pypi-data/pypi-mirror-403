"""Skill tool functions for handling anthropic skills."""

from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from pydantic_ai.toolsets.function import FunctionToolset

from aixtools.logging.logging_config import get_logger
from aixtools.skills.model import ActivateSkillResult, SkillException, SkillSummary
from aixtools.skills.registry import SKILL_CONTAINER_PATH, SkillRegistry

logger = get_logger(__name__)


class SkillTools(TypedDict):
    """Dictionary containing skill tool functions."""

    skill_activate: Callable[[str], ActivateSkillResult]
    skill_list_available: Callable[[], list[SkillSummary]]
    skill_read_file: Callable[[str, str], str]
    skill_exec: Callable[[str, str], str]


def get_skill_tools(registry: SkillRegistry) -> SkillTools:
    """Create tool functions with access to the provided registry.

    Returns a dictionary with closure functions that have access to the registry.
    """

    def skill_activate(skill_name: str) -> ActivateSkillResult:
        """Activate skill by loading definition and returning instructions.

        Container creation happens lazily on first skill_exec call.
        """
        return registry.activate_skill(skill_name)

    def skill_list_available() -> list[SkillSummary]:
        """List all available skills with name and description."""
        return registry.list_skills()

    def skill_read_file(skill_name: str, file_path: str) -> str:
        """Read a file from the skill's folder.

        Args:
            skill_name: Name of the skill
            file_path: Path to the file relative to the skills folder

        Returns:
            File contents or error message
        """
        try:
            skill_source_path = registry.get_skill_source_path(skill_name)
        except SkillException:
            return f"Error: Skill '{skill_name}' not found."

        # Resolve paths to absolute, normalized forms to prevent path traversal
        try:
            resolved_skill_path = skill_source_path.resolve()
            resolved_file_path = (skill_source_path / file_path).resolve()
        except (OSError, RuntimeError) as e:
            return f"Error: Invalid file path: {e}"

        # Security check: ensure the resolved path is within the skill directory
        if not resolved_file_path.is_relative_to(resolved_skill_path):
            return "Error: Access denied - path outside of the skill directory."

        if not resolved_file_path.exists():
            return f"Error: File '{file_path}' not found in skill '{skill_name}'."

        with open(resolved_file_path, "r", encoding="utf-8") as f:
            return f.read()

    def skill_exec(skill_name: str, command: str | list[str]) -> str:
        """Execute command in skill's sandbox container.

        Container is created lazily on first execution if it doesn't exist.
        """
        try:
            session_proxy = registry.ensure_sandbox(skill_name)
        except SkillException as e:
            return f"Error: {e}"
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize sandbox for skill %s: %s", skill_name, e)
            return f"Error: Failed to create sandbox container for skill '{skill_name}': {e}"

        try:
            result = session_proxy.execute_command(
                command=command,
                working_dir=Path(SKILL_CONTAINER_PATH) / skill_name,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            if result.exit_code != 0:
                output += f"\nExit code: {result.exit_code}"
            return output
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to execute command in skill %s: %s", skill_name, e)
            return f"Error executing command: {e}"

    return SkillTools(
        skill_activate=skill_activate,
        skill_list_available=skill_list_available,
        skill_read_file=skill_read_file,
        skill_exec=skill_exec,
    )


def get_skill_toolsets(skill_registry: SkillRegistry, max_retries: int = 1) -> list[FunctionToolset]:
    """Get skill toolsets wrapped in pydantic-ai FunctionToolset.

    Retrieves skills from the registry and wraps them into a FunctionToolset for use with pydantic-ai agents.

    Args:
        skill_registry: The skill registry containing available skills
        max_retries: Maximum number of retries for tool execution (default: 1)

    Returns:
        list[FunctionToolset]: A list containing one FunctionToolset with all skill tools
    """
    skill_tools = get_skill_tools(skill_registry)
    skills_toolset = FunctionToolset(tools=[*skill_tools.values()], max_retries=max_retries)
    return [skills_toolset]
