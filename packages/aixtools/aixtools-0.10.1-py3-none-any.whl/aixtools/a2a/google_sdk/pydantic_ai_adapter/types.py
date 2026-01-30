"""Types for Google SDK integration in A2A."""

from typing import Callable, Optional

from a2a.server.agent_execution import AgentExecutor
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import AbstractToolset
from pydantic_ai.tools import ToolFuncEither
from sqlalchemy.ext.asyncio import AsyncEngine

from aixtools.skills.registry import SkillRegistry

AgentExecutorFactory = Callable[[Optional[AsyncEngine]], AgentExecutor]
SystemPromptFactory = Callable[[SkillRegistry | None], str]
SkillRegistryFactory = Callable[[], SkillRegistry]


class AgentParameters(BaseModel):
    """Parameters for configuring the Pydantic AI agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    system_prompt: str | None = Field(None, description="Static system prompt for the agent")
    system_prompt_fn: SystemPromptFactory | None = Field(
        None, description="Function to generate system prompt dynamically"
    )
    mcp_servers: list[str]
    skills_registry_factory: SkillRegistryFactory | None = Field(None, description="Skill registry factory")
    tools: list[ToolFuncEither] = Field(default_factory=list, description="Additional tools for the agent")
    toolsets: list[AbstractToolset] = Field(default_factory=list, description="Toolsets for the agent")


class RunOutput(BaseModel):
    """Output of the pydantic ai agent run."""

    is_task_failed: bool
    is_task_in_progress: bool
    is_input_required: bool
    output: str
    created_artifacts_paths: list[str]
