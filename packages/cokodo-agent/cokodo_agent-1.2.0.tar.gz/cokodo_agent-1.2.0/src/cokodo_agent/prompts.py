"""Interactive prompts for configuration."""

from typing import Any, Dict, Optional, cast

import questionary
from questionary import Style

from cokodo_agent.config import AI_TOOLS, TECH_STACKS

# Custom style
custom_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ]
)


def prompt_config(
    default_name: Optional[str] = None,
    default_stack: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Interactive prompts for project configuration.

    Args:
        default_name: Default project name
        default_stack: Default tech stack

    Returns:
        Configuration dictionary
    """

    # Project name
    project_name = questionary.text(
        "Project name:",
        default=default_name or "",
        style=custom_style,
    ).ask()

    if project_name is None:
        raise KeyboardInterrupt("User cancelled")

    # Description
    description = questionary.text(
        "Brief description (optional):",
        default="",
        style=custom_style,
    ).ask()

    if description is None:
        raise KeyboardInterrupt("User cancelled")

    # Tech stack
    stack_choices = [questionary.Choice(title=name, value=key) for key, name in TECH_STACKS.items()]

    default_stack_value = default_stack if default_stack in TECH_STACKS else None

    tech_stack = questionary.select(
        "Primary tech stack:",
        choices=stack_choices,
        default=default_stack_value,
        style=custom_style,
    ).ask()

    if tech_stack is None:
        raise KeyboardInterrupt("User cancelled")

    # AI tools
    tool_choices = [
        questionary.Choice(
            title=cast(str, info["name"]),
            value=key,
            checked=(key == "cokodo"),  # Only Cokodo is default
        )
        for key, info in AI_TOOLS.items()
    ]

    ai_tools = questionary.checkbox(
        "AI tools to configure (at least one required):",
        choices=tool_choices,
        style=custom_style,
        validate=lambda x: len(x) > 0 or "Please select at least one option",
    ).ask()

    if ai_tools is None:
        raise KeyboardInterrupt("User cancelled")

    # Ensure at least one is selected
    if not ai_tools:
        ai_tools = ["cokodo"]  # Fallback to cokodo

    return {
        "project_name": project_name,
        "description": description,
        "tech_stack": tech_stack,
        "ai_tools": ai_tools,
    }
