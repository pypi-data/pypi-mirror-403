"""Skills related system prompt generation."""

from aixtools.skills.registry import SkillRegistry

SKILL_SYSTEM_PROMPT = """
# Skills

Available Skills:
_skill_list_

To activate the skill and get further instructions, use skill_activate(skill_name) tool and make decisions based on
retrieved information.
DO NOT try to activate a skill with skill_activate tool until you discovered that the skill is needed for the task.

In order to read files related to the skill use skill_read_file tool.
Follow the received instructions carefully.

In order to launch the script of the skill use skill_exec tool.
Pass skill name as first argument and command to trigger the skill script. Command would look like (called from the
/skills/_skill_name_ dir)
```bash
python3 ./scripts/some_task.py --arg1 val1 --arg2 val2
```
"""


def get_skills_system_prompt(registry: SkillRegistry) -> str:
    """Generate a system prompt section describing available skills.

    Returns a formatted string that can be included in a system prompt to inform
    the LLM about available skills and how to use them.
    """
    skills = registry.list_skills()
    if not skills:
        return ""

    skills_list = [f"- {skill.name}: {skill.description}\n" for skill in skills]

    return SKILL_SYSTEM_PROMPT.replace("_skill_list_", "".join(skills_list))
