# Beer Agenda

## Prerequisites

- [mise](https://mise.jdx.dev/) - Runtime version manager

## Setup

1. Install mise (if not already installed):

```bash
curl https://mise.run | sh
```

2. Trust and install the project tools:

```bash
mise trust
mise install
```

3. Install Python dependencies:

```bash
uv sync
```

4. Install pre-commit hooks:

```bash
uv run pre-commit install
```

5. Setup crawl4ai (install Playwright and browsers):

```bash
crawl4ai-setup
```

6. Setup Ollama (start server and download model):

```bash
ollama serve &
ollama pull llama3.1:8b
```

## Run

Run pre-commit on all files manually:

```bash
uv run pre-commit run --all-files
```

Run crawler:

```bash
uv run python main.py
```

## Commits

Use commitizen for conventional commits:

```bash
uv run cz commit
```
