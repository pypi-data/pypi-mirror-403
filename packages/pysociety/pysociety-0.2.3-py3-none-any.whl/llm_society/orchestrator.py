"""Orchestrator that manages multi-agent debates."""

import os

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from .config import get_config
from .prompts import ORCHESTRATOR_PROMPT, SUBAGENT_SUFFIX
from .schemas import GeneratedPrompts


class Orchestrator:  # pylint: disable=too-few-public-methods
    """Main orchestrator agent that manages sub-agents."""

    def __init__(
        self,
        generated_prompts: GeneratedPrompts,
        main_agent_model: str | None = None,
        sub_agent_model: str | None = None,
    ):
        config = get_config()

        self.main_agent_model = main_agent_model or config["main_agent_model"]
        self.sub_agent_model = sub_agent_model or config["sub_agent_model"]

        # Store generated prompts
        self.generated_prompts = generated_prompts

        # Build agent info from generated prompts
        self.agent_info = {
            p.name.capitalize(): p.prompt for p in generated_prompts.subagents
        }

        # Build agent roster string
        self.agent_roster = self._build_agent_roster()

        # Create the deep agent with subagents
        self._agent = self._create_agent()

    def _build_agent_roster(self) -> str:
        """Build a string describing all agents for prompts."""
        lines = [f"- {name}" for name in self.agent_info.keys()]
        return "\n".join(lines)

    def _build_roster_for_agent(self, exclude_name: str) -> str:
        """Build roster excluding a specific agent."""
        lines = [f"- {name}" for name in self.agent_info.keys() if name != exclude_name]
        return "\n".join(lines)

    def _build_agent_names_list(self) -> str:
        """Build list of agent names for the task tool instruction."""
        names = [name.lower() for name in self.agent_info.keys()]
        return f"- {', '.join(names)} (your generated agents)"

    def _create_subagent_config(self, name: str) -> dict:
        """Create configuration for a sub-agent."""
        base_prompt = self.agent_info[name]
        system_prompt = base_prompt + SUBAGENT_SUFFIX.format(
            agent_roster=self._build_roster_for_agent(name),
        )

        return {
            "name": name.lower(),
            "model": self.sub_agent_model,
            "description": f"Talk to {name}",
            "system_prompt": system_prompt,
            "tools": [],
        }

    def _create_agent(self):
        """Create the main orchestrator agent with sub-agents."""
        # Build the orchestrator system prompt
        first_agent_name = list(self.agent_info.keys())[0].lower()
        system_prompt = ORCHESTRATOR_PROMPT.format(
            agent_roster=self.agent_roster,
            agent_names_list=self._build_agent_names_list(),
            first_agent_name=first_agent_name,
        )

        # Create subagent configs
        subagents = [
            self._create_subagent_config(name) for name in self.agent_info.keys()
        ]

        # Create the deep agent
        return create_deep_agent(
            model=self.main_agent_model,
            system_prompt=system_prompt,
            subagents=subagents,
            backend=FilesystemBackend(root_dir=os.getcwd(), virtual_mode=True),
        )

    def run(self, initial_prompt: str = "Start the simulation!") -> dict:
        """
        Run the simulation.

        Args:
            initial_prompt: The initial prompt to kick off the simulation

        Returns:
            The final result from the orchestrator
        """
        result = self._agent.invoke({"messages": [("user", initial_prompt)]})
        return result
