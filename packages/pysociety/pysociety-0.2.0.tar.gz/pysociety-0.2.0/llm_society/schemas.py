from pydantic import BaseModel


class SubAgentPrompt(BaseModel):
    name: str
    prompt: str


class GeneratedPrompts(BaseModel):
    subagents: list[SubAgentPrompt]
