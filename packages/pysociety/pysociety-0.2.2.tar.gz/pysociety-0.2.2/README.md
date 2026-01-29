# A Society of Agents

[![Pylint](https://github.com/zzzrbx/llm-society/actions/workflows/pylint.yml/badge.svg)](https://github.com/zzzrbx/llm-society/actions/workflows/pylint.yml)
[![PyPI](https://img.shields.io/pypi/v/pysociety)](https://pypi.org/project/pysociety/)

<p align="center">
  <img src=".github/banner.png" alt="LLM Society - AI agents in philosophical debate" width="800">
</p>

Inspired by Marvin Minsky's [Society of Mind](https://en.wikipedia.org/wiki/Society_of_Mind), a multi-agent simulation where AI personalities debate questions from different perspectives. Ask a question, specify the viewpoints you want, and watch the debate unfold.

## What it does

1. You provide a question and the perspectives you want represented
2. AI generates distinct agent personalities for each perspective
3. An orchestrator facilitates debate between the agents
4. Agents discuss, disagree, and build on each other's arguments

## Installation

```bash
pip install pysociety
```

or

```bash
uv add pysociety
```

## Quick Start

Create a `.env` file with your API key:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

### Run a debate

```bash
uv run python -m llm_society "What is the meaning of life? I want an optimistic view and a pessimistic one."
```

### More examples

```bash
# Ethics debate
uv run python -m llm_society "$(cat examples/trolley_problem.txt)"

# Philosophy
uv run python -m llm_society "$(cat examples/free_will.txt)"

# Social issues
uv run python -m llm_society "$(cat examples/wealth_inequality.txt)"
```

## Example Questions

| File | Topic | Perspectives |
|------|-------|--------------|
| `meaning_of_life.txt` | Meaning of life | Optimist, Pessimist |
| `trolley_problem.txt` | Trolley problem | Utilitarian, Deontologist, Virtue ethicist |
| `free_will.txt` | Free will | Determinist, Libertarian, Compatibilist |
| `wealth_inequality.txt` | Wealth inequality | Libertarian, Socialist, Rawlsian, Communitarian |
| `animal_rights.txt` | Animal rights | Peter Singer, Traditionalist, Environmental ethicist |
| `civil_disobedience.txt` | Civil disobedience | Thoreau, MLK, Legal positivist, Conservative |

## Optional Configuration

You can customize models in `.env`:

```bash
# Main orchestrator model
MAIN_AGENT_MODEL=anthropic:claude-opus-4-5-20251101

# Sub-agent models
SUB_AGENT_MODEL=anthropic:claude-sonnet-4-5-20250929

# Prompt generation model
PROMPT_GENERATOR_MODEL=anthropic/claude-opus-4-5-20251101
```
