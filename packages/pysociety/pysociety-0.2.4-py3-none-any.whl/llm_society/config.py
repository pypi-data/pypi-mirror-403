"""Configuration management for LLM Society."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_config():
    """Load configuration from environment variables."""
    return {
        "main_agent_model": os.getenv(
            "MAIN_AGENT_MODEL", "anthropic:claude-opus-4-5-20251101"
        ),
        "sub_agent_model": os.getenv(
            "SUB_AGENT_MODEL", "anthropic:claude-sonnet-4-5-20250929"
        ),
        "prompt_generator_model": os.getenv(
            "PROMPT_GENERATOR_MODEL", "anthropic/claude-opus-4-5-20251101"
        ),
    }
