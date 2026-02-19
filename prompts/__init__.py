"""Prompt templates for agents."""

from .chat_prompts import (
    ROUTER_PROMPT,
    TASK_PROMPTS,
    get_task_prompt,
    # Legacy exports
    get_prompt,
    ACTION_PROMPTS,
    CHAT_SYSTEM_PROMPT,
)

__all__ = [
    "ROUTER_PROMPT",
    "TASK_PROMPTS",
    "get_task_prompt",
    # Legacy
    "get_prompt",
    "ACTION_PROMPTS",
    "CHAT_SYSTEM_PROMPT",
]
