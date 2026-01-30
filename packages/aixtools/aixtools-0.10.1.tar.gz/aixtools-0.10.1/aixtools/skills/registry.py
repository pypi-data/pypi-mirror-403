"""Registry for managing loaded skills per user session."""

from pathlib import Path

import frontmatter
from podkit import SessionProxy, get_docker_session
from podkit.core.models import ContainerConfig, Mount
from pydantic import BaseModel, ConfigDict, Field

from aixtools.context import SessionIdTuple
from aixtools.logging.logging_config import get_logger
from aixtools.server import get_session_id_tuple
from aixtools.skills.model import ActivateSkillResult, Skill, SkillException, SkillResult, SkillSummary
from aixtools.utils.config import DATA_DIR, HOST_DATA_DIR

logger = get_logger(__name__)

SKILL_FILE_NAME = "SKILL.md"
SKILLS_WORKSPACE_DIR = "skills"
METADATA_SANDBOX_IMAGE = "sandbox_image"
SKILL_CONTAINER_PATH = "/skills"


class _SkillRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    skill: Skill = Field(description="Parsed skill definition")
    source_path: Path = Field(description="Path to the skill source")
    is_activated: bool = Field(default=False, description="Whether the skill has been activated")
    source_path_host: Path | None = Field(default=None, description="Path to the skill source host")
    session_proxy: SessionProxy | None = Field(default=None, description="Skill session proxy to sandbox")


class SkillRegistry:
    """Registry for managing skills loaded from SKILL.md files."""

    def __init__(self, skills_folder: Path | str | None = None, skills_folder_host: Path | str | None = None):
        self._skill_records: dict[str, _SkillRecord] = {}
        if skills_folder:
            self._load_skills_from_folder(
                folder=Path(skills_folder),
                folder_host=Path(skills_folder_host) if skills_folder_host else None,
            )

    def activate_skill(self, skill_name: str) -> ActivateSkillResult:
        """Activate a skill by loading its definition and returning instructions.

        Note: Containers are created lazily when skill_exec is first called.
        """
        record = self._skill_records.get(skill_name)
        if not record:
            return ActivateSkillResult(success=False, message=f"Skill '{skill_name}' not found.")
        logger.info("Activated skill: %s", skill_name)
        record.is_activated = True
        return ActivateSkillResult(
            success=True,
            skill=SkillResult(**record.skill.model_dump(exclude={"metadata"})),
        )

    def get_session_proxy(self, skill_name: str) -> SessionProxy:
        """Get session proxy for skill's container in current session."""
        return self._get_skill_record(skill_name).session_proxy

    def get_skill_source_path(self, skill_name: str) -> Path | None:
        """Get the source path for a skill."""
        return self._get_skill_record(skill_name).source_path

    def ensure_sandbox(self, skill_name: str) -> SessionProxy:
        """Ensure sandbox container exists for this skill and session, creating if needed.

        Raises:
            Exception: If skill not found or container creation fails
        """
        record = self._get_skill_record(skill_name)
        if record.session_proxy:
            logger.info("Reusing existing sandbox for skill: %s", skill_name)
            return record.session_proxy

        (user_id, session_id) = get_session_id_tuple()
        session_proxy = _start_sandbox((user_id, session_id), record)
        record.session_proxy = session_proxy
        logger.info(
            "Started sandbox for skill: %s, image: %s, user: %s, session: %s",
            skill_name,
            record.skill.metadata.get(METADATA_SANDBOX_IMAGE),
            user_id,
            session_id,
        )

        return session_proxy

    def get_skill(self, name: str) -> Skill:
        """Get a skill by its name."""
        return self._get_skill_record(name).skill

    def list_skills(self) -> list[SkillSummary]:
        """Return list of available skills with name and description."""
        return [
            SkillSummary(name=record.skill.name, description=record.skill.description)
            for record in self._skill_records.values()
        ]

    def load_skill(self, path: Path, host_path: Path | None = None):
        """Load a skill compatible with anthropic skills specs: https://agentskills.io/specification"""
        try:
            skill_file = path / SKILL_FILE_NAME
            skill_meta_data = frontmatter.load(str(skill_file))
            instructions = skill_meta_data.content.strip()

            raw_metadata = skill_meta_data.metadata.get("metadata", {})
            metadata = {k: str(v) for k, v in raw_metadata.items()} if isinstance(raw_metadata, dict) else {}

            skill = Skill(
                name=str(skill_meta_data["name"]),
                description=str(skill_meta_data["description"]),
                instructions=instructions,
                metadata=metadata,
            )
            self._skill_records[skill.name] = _SkillRecord(
                skill=skill,
                source_path=path,
                source_path_host=host_path,
            )
            logger.info("Loaded skill: %s from %s", skill.name, path)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to load skill from %s: %s", path, e)

    def _get_skill_record(self, skill_name: str) -> _SkillRecord:
        """Get the skill record by name."""
        record = self._skill_records.get(skill_name)
        if not record:
            raise SkillException(f"Skill '{skill_name}' not found.")
        return record

    def _load_skills_from_folder(self, folder: Path, folder_host: Path | None):
        """Load all skills from a folder containing skill subdirectories."""
        if not folder.exists():
            logger.error("Skills folder does not exist: %s", folder)
            raise SkillException("Skills folder does not exist")

        if not folder.is_dir():
            raise SkillException("Skill path is not a directory")

        for skill_dir in folder.iterdir():
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / SKILL_FILE_NAME).exists():
                logger.warning(f"{SKILL_FILE_NAME} does not exist: %s", skill_dir)
                continue

            skill_host_dir = _to_host_path(
                skill_source=skill_dir,
                skills_dir_base=folder,
                skills_dir_host=folder_host,
            )
            self.load_skill(skill_dir, skill_host_dir)


def _start_sandbox(ctx: SessionIdTuple, record: _SkillRecord) -> SessionProxy:
    """Start sandbox container for the skill if sandbox_image is configured."""

    sandbox_image = record.skill.metadata.get(METADATA_SANDBOX_IMAGE)
    if not sandbox_image:
        raise SkillException(f"No sandbox_image configured for skill: {record.skill.name}")

    user_id, session_id = ctx
    config = ContainerConfig(
        image=sandbox_image,
        container_lifetime_seconds=300,
        volumes=[
            Mount(
                source=record.source_path_host or record.source_path,
                target=Path(SKILL_CONTAINER_PATH) / record.skill.name,
                read_only=True,
            ),
        ],
    )

    return get_docker_session(
        user_id=user_id,
        session_id=session_id,
        workspace=DATA_DIR,
        workspace_host=HOST_DATA_DIR,
        config=config,
    )


def _to_host_path(*, skill_source: Path, skills_dir_base: Path, skills_dir_host: Path) -> Path | None:
    """Convert skill source path to host path based on base and host skills directories."""
    if not skills_dir_host:
        return None

    try:
        relative_path = skill_source.relative_to(skills_dir_base)
        return skills_dir_host / relative_path
    except ValueError as e:
        raise SkillException(
            f"Cannot determine host path for skill source {skill_source} not under base {skills_dir_base}"
        ) from e
