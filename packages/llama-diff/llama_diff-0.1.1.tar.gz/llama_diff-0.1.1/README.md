# LlamaDiff

A Python-based code review tool that analyzes git diffs between branches using LLMs.

## License

Licensed under the Apache License, Version 2.0.

## Features

- Compare any two git branches and get AI-powered code review
- Supports multiple LLM providers via litellm:
  - **Ollama** (local, default)
  - **OpenAI** (GPT-4, GPT-4o, etc.)
  - **Anthropic** (Claude)
  - **OpenRouter** (access to many models)

## Installation

### Via pipx (recommended)

```bash
# Run directly without installing
pipx run llama-diff -s feature -t main

# Or install globally
pipx install llama-diff
```

### Via pip

```bash
pip install llama-diff
```

### From source

```bash
git clone https://github.com/ernestp/LlamaDiff.git
cd LlamaDiff
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure your preferred provider:

```bash
cp .env.example .env
```

## Usage

```bash
# Basic usage (compare current branch to main)
llama-diff --source feature-branch --target main

# Using a specific model
llama-diff -s feature -t main --model ollama/codellama

# Using OpenAI
llama-diff -s feature -t main --model gpt-4o

# Review specific files only
llama-diff -s feature -t main --files "*.py"

# Output to file
llama-diff -s feature -t main --output review.md

# Interactive HTML review
llama-diff -s feature -t main --html

# Review uncommitted changes
llama-diff --uncommitted
```

## Model Examples

| Provider | Model Example |
|----------|---------------|
| Ollama | `ollama/llama3.2`, `ollama/codellama` |
| OpenAI | `gpt-5.2`, `gpt-5.1`, `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `claude-sonnet-4.5`, `claude-opus-4.5` |
| OpenRouter | `openrouter/anthropic/claude-sonnet-4.5`, `openrouter/anthropic/claude-opus-4.5` |
