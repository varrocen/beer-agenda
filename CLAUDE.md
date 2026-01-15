# Beer Agenda

Web crawler project to aggregate beer-related events from various sources and generate markdown output.

## IMPORTANT: Validation After Code Changes

**ALWAYS run validation after modifying any code. This is MANDATORY, not optional.**

```bash
# Run JS tests
mise exec -- npm test

# Full validation (run the crawler - takes ~3 minutes)
mise exec -- uv run main.py
```

**DO NOT proceed to other tasks until validation passes.**

## Project Structure

```
beer-agenda/
├── crawlers/
│   ├── facebook.py          # Facebook-specific crawler
│   └── scripts/
│       └── facebook_decline_popups_and_scroll.js  # JS scripts for browser automation
├── extractors/
│   └── events.py            # LLMExtractionStrategy + Pydantic schema
├── models/
│   └── event.py             # Event Pydantic model
├── outputs/
│   ├── events.md            # Generated markdown output
│   └── debug/               # Debug files (when DEBUG=true)
│       └── facebook-events-page-{page_name}.md
├── tests/
│   └── crawlers/
│       └── scripts/
│           ├── facebook_decline_popups_and_scroll.test.js
│           └── fixtures/
├── main.py                  # Entry point
├── pyproject.toml
├── biome.json               # Biome configuration for JS linting/formatting
└── CLAUDE.md
```

### Module Responsibilities

- **crawlers/**: Web crawling logic, one file per source (Facebook, etc.)
- **crawlers/scripts/**: JavaScript files for browser automation (popups, etc.)
- **extractors/**: LLM extraction strategies and configuration
- **models/**: Pydantic data models for validation
- **outputs/**: Generated markdown files
- **outputs/debug/**: Debug files saved when `DEBUG=true` (raw markdown before LLM extraction)
- **tests/**: Test files mirroring the source structure

## Tech Stack

- Python 3.12+
- crawl4ai for web scraping
- Ollama for local LLM inference
- Pydantic for data validation
- uv for dependency management
- mise for tool version management

## Ollama Setup

Ollama is installed via mise. Start the server and download the model:

```bash
# Start Ollama server (in a separate terminal or background)
ollama serve &

# Download the model
ollama pull llama3.1:8b
```

The server must be running on `localhost:11434` before using LLM extraction.

## Debug Mode

Enable debug mode to save raw crawled markdown before LLM extraction. Useful for debugging extraction issues.

```bash
# Run with debug mode enabled
DEBUG=true mise exec -- uv run main.py
```

Debug files are saved to `outputs/debug/` with the naming pattern `facebook-events-page-{page_name}.md`.

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

# Install Node.js dependencies
mise exec -- npm install

# Run JS tests
mise exec -- npm test

# Run JS tests in watch mode
mise exec -- npm run test:watch
```

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
| `llama3.1:8b` | 8B | Good | ~8 Go |
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
    provider="ollama/llama3.1:8b",
    base_url="http://localhost:11434",
)

strategy = LLMExtractionStrategy(
    llm_config=llm_config,
    schema=Event.model_json_schema(),
    instruction="Extract all events from this Facebook page",
)
```

## JavaScript Testing Strategy

We use **Jest** with **CommonJS** for testing browser automation scripts.

### Why Jest + CommonJS?

The scripts in `crawlers/scripts/` are injected into browsers via Playwright (crawl4ai). Playwright doesn't support ES modules (`export`), so scripts must be plain JavaScript.

| Option | Problem |
|--------|---------|
| Vitest | Requires ES modules, incompatible with browser scripts |
| **Jest + CommonJS** | Single file works in both Node.js and browser |

### How it works

Scripts use conditional exports to work in both environments:

```javascript
function findDeclineButton() { /* ... */ }

if (typeof module !== "undefined" && module.exports) {
    // Node.js (Jest) → export functions
    module.exports = { findDeclineButton };
} else {
    // Browser (Playwright) → execute
    declinePopupsAndScroll();
}
```

- **In Node.js**: `module` exists → exports functions for testing
- **In browser**: `module` is undefined → executes the script

### Test structure

```
tests/
└── crawlers/
    └── scripts/
        ├── facebook_decline_popups_and_scroll.test.js
        └── fixtures/
            ├── facebook_cookies_popup.html
            └── facebook_login_popup.html
```

Fixtures contain real Facebook HTML to test selectors against actual markup.

## Output Format

Events are exported as markdown files with the following structure:

```markdown
## Event Title
- **Date:** YYYY-MM-DD HH:MM
- **Organizer:** Organizer name
- **Link:** Original URL
```
