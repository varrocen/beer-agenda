# Configuration Reference

## Table of Contents
1. [BrowserConfig](#browserconfig)
2. [CrawlerRunConfig](#crawlerrunconfig)
3. [LLMConfig](#llmconfig)
4. [CacheMode](#cachemode)
5. [Common Patterns](#common-patterns)

---

## BrowserConfig

Controls browser behavior for the entire crawler session.

```python
from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    # Browser type
    browser_type="chromium",        # chromium|firefox|webkit
    headless=True,                  # Run without visible window

    # Viewport
    viewport_width=1280,
    viewport_height=720,

    # Performance
    text_mode=False,                # Disable images for text-only crawls
    light_mode=False,               # Disable background features

    # Proxy
    proxy_config={
        "server": "http://proxy:8080",
        "username": "user",
        "password": "pass"
    },
    # Or simple: proxy="http://proxy:8080"

    # User agent
    user_agent="Mozilla/5.0 ...",
    user_agent_mode="random",       # Randomize to avoid detection

    # Persistence
    use_persistent_context=False,
    user_data_dir=None,             # Path for persistent browser data

    # Cookies & Headers (initial)
    cookies=[{"name": "session", "value": "abc", "domain": ".example.com"}],
    headers={"Authorization": "Bearer token"},

    # Stealth mode (anti-detection)
    use_managed_browser=False,
    enable_stealth=True,            # Enable playwright-stealth

    # Debugging
    verbose=True,
    debugging_port=9222,

    # Extra browser args
    extra_args=["--disable-extensions", "--no-sandbox"]
)
```

---

## CrawlerRunConfig

Controls behavior for each `arun()` call.

```python
from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai import DefaultMarkdownGenerator, PruningContentFilter
from crawl4ai import JsonCssExtractionStrategy

run_config = CrawlerRunConfig(
    # === Content Selection ===
    css_selector=None,              # Focus on specific element
    target_elements=["#main", ".sidebar"],  # Multiple targets
    excluded_tags=["nav", "footer", "header", "aside"],
    exclude_external_links=True,
    exclude_domains=["ads.com", "tracking.com"],
    word_count_threshold=10,        # Min words per block

    # === Markdown Generation ===
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(
            threshold=0.5,          # Pruning aggressiveness
            threshold_type="fixed"
        )
    ),

    # === Extraction Strategy ===
    extraction_strategy=JsonCssExtractionStrategy(schema),

    # === JavaScript Execution ===
    js_code="document.querySelector('.load-more').click();",
    # Or list: js_code=["code1", "code2"]
    wait_for="css:.loaded-content",  # Wait for element: css:selector or js:expression
    delay_before_return_html=1.0,    # Seconds to wait after JS

    # === Session Management ===
    session_id="my_session",         # Reuse browser tab across calls
    js_only=False,                   # Skip navigation, just run JS

    # === Caching ===
    cache_mode=CacheMode.BYPASS,     # See CacheMode section

    # === Timeouts ===
    page_timeout=30000,              # Page load timeout (ms)

    # === Output Options ===
    screenshot=False,                # Capture screenshot
    pdf=False,                       # Generate PDF

    # === Processing ===
    process_iframes=False,           # Extract iframe content
    remove_overlay_elements=True,    # Remove modals/popups

    # === Verbose ===
    verbose=True
)
```

---

## LLMConfig

Configuration for LLM-based extraction and filtering.

```python
from crawl4ai import LLMConfig

# OpenAI
openai_config = LLMConfig(
    provider="openai/gpt-4o",
    api_token="sk-...",             # Or "env:OPENAI_API_KEY"
    temperature=0.0,
    max_tokens=4000
)

# Anthropic
anthropic_config = LLMConfig(
    provider="anthropic/claude-3-sonnet-20240229",
    api_token="sk-ant-...",
    temperature=0.0
)

# Ollama (local)
ollama_config = LLMConfig(
    provider="ollama/llama3.3",
    api_token=None,                 # Not needed
    base_url="http://localhost:11434"
)

# Google Gemini
gemini_config = LLMConfig(
    provider="gemini/gemini-1.5-pro",
    api_token="env:GEMINI_API_TOKEN"
)

# Custom endpoint
custom_config = LLMConfig(
    provider="openai/custom-model",
    api_token="token",
    base_url="https://my-llm-server.com/v1"
)
```

---

## CacheMode

Control caching behavior to balance speed vs freshness.

```python
from crawl4ai import CacheMode

# Options:
CacheMode.ENABLED      # Read and write cache (default)
CacheMode.DISABLED     # No caching at all
CacheMode.BYPASS       # Skip reading cache, but write new results
CacheMode.READ_ONLY    # Read cache only, don't write
CacheMode.WRITE_ONLY   # Write only, don't read existing
```

Usage:
```python
config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS  # Always fetch fresh content
)
```

---

## Common Patterns

### Fast Markdown Extraction

```python
browser_config = BrowserConfig(
    headless=True,
    text_mode=True,         # Skip images
    light_mode=True         # Minimal features
)

run_config = CrawlerRunConfig(
    excluded_tags=["nav", "footer", "header", "aside", "script", "style"],
    word_count_threshold=10,
    cache_mode=CacheMode.ENABLED
)
```

### Stealth Mode (Anti-Detection)

```python
browser_config = BrowserConfig(
    headless=True,
    user_agent_mode="random",
    enable_stealth=True,
    extra_args=["--disable-blink-features=AutomationControlled"]
)

run_config = CrawlerRunConfig(
    delay_before_return_html=2.0,   # Human-like delay
    remove_overlay_elements=True
)
```

### With Proxy Authentication

```python
browser_config = BrowserConfig(
    proxy_config={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    }
)
```

### Screenshot + PDF Capture

```python
run_config = CrawlerRunConfig(
    screenshot=True,
    pdf=True,
    wait_for="css:body",
    delay_before_return_html=1.0
)

result = await crawler.arun(url, config=run_config)
# result.screenshot = base64 string
# result.pdf = bytes
```

### Dynamic Content with Scroll

```python
js_scroll = """
(async () => {
    for (let i = 0; i < 5; i++) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1000));
    }
})();
"""

run_config = CrawlerRunConfig(
    js_code=js_scroll,
    wait_for="js:() => document.querySelectorAll('.item').length > 20",
    delay_before_return_html=2.0
)
```

### Login Flow

```python
# Step 1: Login
login_config = CrawlerRunConfig(
    session_id="auth_session",
    js_code="""
        document.querySelector('#username').value = 'user';
        document.querySelector('#password').value = 'pass';
        document.querySelector('#login-btn').click();
    """,
    wait_for="css:.dashboard"
)

# Step 2: Crawl authenticated pages
crawl_config = CrawlerRunConfig(
    session_id="auth_session",  # Reuse session
    css_selector=".content"
)
```
