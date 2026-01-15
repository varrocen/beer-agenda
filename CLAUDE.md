# Beer Agenda

Web crawler project to aggregate beer-related events from various sources and generate markdown output.

## Project Structure

```
beer-agenda/
├── crawlers/
│   └── facebook.py          # Facebook-specific crawler
├── extractors/
│   └── events.py            # LLMExtractionStrategy + Pydantic schema
├── models/
│   └── event.py             # Event Pydantic model
├── outputs/
│   └── events.md            # Generated markdown output
├── main.py                  # Entry point
├── pyproject.toml
└── CLAUDE.md
```

### Module Responsibilities

- **crawlers/**: Web crawling logic, one file per source (Facebook, etc.)
- **extractors/**: LLM extraction strategies and configuration
- **models/**: Pydantic data models for validation
- **outputs/**: Generated markdown files

## Tech Stack

- Python 3.12+
- crawl4ai for web scraping
- Ollama for local LLM inference
- Pydantic for data validation
- uv for dependency management
- mise for tool version management

## Development Commands

Always use `mise exec --` to run uv commands:

```bash
# Add a dependency
mise exec -- uv add <package>

# Add a dev dependency
mise exec -- uv add --dev <package>

# Run a script
mise exec -- uv run <script.py>

# Run pre-commit
mise exec -- uv run pre-commit run --all-files

# Commit with conventional commits
mise exec -- uv run cz commit
```

## Development Workflow

After modifying any code, always run the main script to verify there are no errors:

```bash
mise exec -- uv run main.py
```

If an error occurs, fix it before continuing with other tasks.

## Crawl4AI Configuration

### General Anti-Detection Setup

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
  headless=True,
  enable_stealth=True,         # Enable playwright-stealth
  user_agent_mode="random",    # Rotate user-agent
  viewport_width=1920,
  viewport_height=1080,
)

run_config = CrawlerRunConfig(
  mean_delay=2.0,
  delay_before_return_html=1.0,
)
```

### Facebook-Specific Configuration

Facebook has aggressive anti-bot protections. Use this configuration:

```python
browser_config = BrowserConfig(
  headless=False,              # Visible browser = harder to detect
  enable_stealth=True,         # Enable playwright-stealth
  user_agent_mode="random",
  viewport_width=1920,
  viewport_height=1080,
  use_persistent_context=True, # Preserve cookies/session
)

run_config = CrawlerRunConfig(
  simulate_user=True,          # Simulate human behavior
  mean_delay=3.0,
  delay_before_return_html=2.0,
)
```

**Progressive strategy if blocked:**

1. `enable_stealth=True` alone
2. Add `headless=False`
3. Add `simulate_user=True` + delays
4. Use proxy via `proxy_config`

**Facebook event URLs:**

- Page events: `https://www.facebook.com/{page_name}/events`
- Single event: `https://www.facebook.com/events/{event_id}`

## Data Extraction Strategy

We use **LLM-based extraction** with Ollama instead of CSS-based extraction.

### Why LLM-based extraction?

| Approach | Pros | Cons |
|----------|------|------|
| **CSS-based** | Fast, free, deterministic | Fragile, breaks when HTML changes |
| **LLM-based** | Robust, understands context, works on messy HTML | Slower, requires LLM |

**For Facebook specifically**, LLM-based extraction is the right choice because:

1. Facebook HTML is heavily obfuscated (random class names like `x1lliihq x6ikm8r`)
2. CSS selectors would break frequently as Facebook updates their markup
3. The crawled markdown loses DOM structure but keeps readable text
4. LLM can semantically understand and extract events reliably

### Why Ollama?

- **Free**: No API costs, runs locally
- **Private**: Data never leaves your machine
- **No dependency**: Works offline, no API keys needed

Recommended models for extraction:

| Model | Size | Quality | RAM |
|-------|------|---------|-----|
| `llama3.2:3b` | 3B | Correct | ~4 Go |
| `qwen2.5:7b` | 7B | Very good | ~8 Go |

### Pydantic Schema

We use Pydantic to define the expected data structure. This schema is passed to the LLM to ensure consistent output format.

```python
from pydantic import BaseModel

class Event(BaseModel):
    date: str
    title: str
    organizer: str
    link: str
```

### Extraction Configuration

```python
from crawl4ai import LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

llm_config = LLMConfig(
    provider="ollama/llama3.2",
    base_url="http://localhost:11434",
)

strategy = LLMExtractionStrategy(
    llm_config=llm_config,
    schema=Event.model_json_schema(),
    instruction="Extract all events from this Facebook page",
)
```

## Output Format

Events are exported as markdown files with the following structure:

```markdown
## Event Title
- **Date:** YYYY-MM-DD HH:MM
- **Organizer:** Organizer name
- **Link:** Original URL
```
