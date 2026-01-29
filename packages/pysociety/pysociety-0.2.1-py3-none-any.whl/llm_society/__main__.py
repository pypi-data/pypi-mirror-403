"""CLI entry point for running LLM Society simulations."""

import sys

from .orchestrator import Orchestrator
from .prompt_generator import generate_prompts


def main():
    """Run the LLM Society simulation with a user-provided question."""
    # Get question from CLI args
    if len(sys.argv) < 2:
        print('Usage: python -m llm_society "Your question here"')
        sys.exit(1)

    question = sys.argv[1]

    print("Generating subagent prompts...")
    try:
        generated_prompts = generate_prompts(question)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error generating prompts: {e}")
        sys.exit(1)

    if not generated_prompts.subagents:
        print("Error: No subagents were generated")
        sys.exit(1)

    print(f"Created {len(generated_prompts.subagents)} subagents:")
    for agent in generated_prompts.subagents:
        print(f"  - {agent.name}")

    print("=" * 50)
    print("Starting LLM Society simulation...")

    orchestrator = Orchestrator(generated_prompts=generated_prompts)

    # Append standard message to question
    initial_prompt = (
        f"{question}\n\nBegin the simulation! Wake up all agents and let them interact."
    )

    result = orchestrator.run(initial_prompt)

    print("=" * 50)
    print("Simulation complete!")

    # Print final messages
    messages = result.get("messages", [])
    if messages:
        print("\nFinal orchestrator message:")
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            print(last_message.content)
        else:
            print(str(last_message))


if __name__ == "__main__":
    main()
