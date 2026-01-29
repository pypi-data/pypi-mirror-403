"""Generate subagent prompts dynamically using the Anthropic API."""

import instructor

from .config import get_config
from .schemas import GeneratedPrompts


def generate_prompts(question: str, model: str | None = None) -> GeneratedPrompts:
    """Generate subagent prompts based on user question."""
    if model is None:
        model = get_config()["prompt_generator_model"]
    client = instructor.from_provider(model)

    system_prompt = """You are a prompt engineer. Given a user question, generate \
subagent prompts for a multi-agent simulation.

Each subagent should have:
- A unique name (lowercase, single word)
- A personality prompt that defines how they think and respond

The subagents should represent different perspectives relevant to the question.
The number of subagents depends on what the user asks for in their question."""

    resp = client.create(
        response_model=GeneratedPrompts,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )
    return resp
