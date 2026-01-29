"""Pydantic schemas for generated prompts."""

from pydantic import BaseModel


class SubAgentPrompt(BaseModel):
    """A single subagent's name and personality prompt."""

    name: str
    prompt: str


class GeneratedPrompts(BaseModel):
    """Collection of generated subagent prompts."""

    subagents: list[SubAgentPrompt]
