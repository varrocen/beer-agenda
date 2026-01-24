---
name: crawl4ai
description: Web crawling and scraping with Crawl4AI - an open-source, LLM-friendly crawler. Use when Claude needs to write Python code for web scraping, data extraction from websites, converting web pages to Markdown, structured data extraction (JSON) via CSS/XPath/LLM strategies, crawling dynamic JavaScript-rendered pages, or building AI/RAG data pipelines from web content. Triggers on terms like "crawl", "scrape", "web extraction", "crawl4ai", or requests to extract data from URLs.
---

# Crawl4AI Skill

Crawl4AI is an open-source, asynchronous web crawler optimized for LLM and AI workflows. It converts web pages to clean Markdown and extracts structured JSON data.

## Installation

```bash
pip install crawl4ai
crawl4ai-setup  # Install Playwright browsers
```

## Quick Start

### Basic Crawl (Markdown Output)

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown.raw_markdown)  # Clean markdown
        print(result.markdown.fit_markdown)  # Filtered/pruned markdown

asyncio.run(main())
```

### With Configuration

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import DefaultMarkdownGenerator, PruningContentFilter

async def main():
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720
    )

    run_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
        ),
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
        excluded_tags=["nav", "footer", "header"]
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://example.com", config=run_config)
        print(result.markdown.fit_markdown)

asyncio.run(main())
```

## Extraction Strategies

Choose the right strategy based on data structure:

| Data Type | Strategy | When to Use |
|-----------|----------|-------------|
| Structured/Repeating | `JsonCssExtractionStrategy` | Product lists, tables, consistent HTML patterns |
| Structured/Complex XPath | `JsonXPathExtractionStrategy` | When CSS selectors are insufficient |
| Unstructured/Semantic | `LLMExtractionStrategy` | Natural language, complex reasoning needed |
| Pattern-based | `RegexExtractionStrategy` | Emails, phones, prices, dates |

### CSS Extraction (No LLM)

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy
import json

schema = {
    "name": "Products",
    "baseSelector": "div.product-card",
    "fields": [
        {"name": "title", "selector": "h2.title", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}
    ]
}

async def extract_products(url):
    strategy = JsonCssExtractionStrategy(schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config)
        return json.loads(result.extracted_content)
```

### Auto-Generate Schema with LLM (One-Time Cost)

```python
from crawl4ai import JsonCssExtractionStrategy, LLMConfig

# Sample HTML from the target page
html = "<div class='product'><h2>Laptop</h2><span class='price'>$999</span></div>"

# Generate schema (one-time LLM call)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="your-token")
)

# Reuse schema for fast, LLM-free extraction
strategy = JsonCssExtractionStrategy(schema)
```

### LLM Extraction (For Complex/Unstructured Data)

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import LLMExtractionStrategy, LLMConfig
from pydantic import BaseModel

class Article(BaseModel):
    title: str
    summary: str
    key_points: list[str]

async def extract_with_llm(url):
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider="openai/gpt-4o", api_token="your-token"),
        schema=Article.model_json_schema(),
        instruction="Extract the main article content"
    )
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config)
        return json.loads(result.extracted_content)
```

## Dynamic Pages (JavaScript)

### Execute JS Before Extraction

```python
config = CrawlerRunConfig(
    js_code="document.querySelector('.load-more').click();",
    wait_for="css:.loaded-content",  # Wait for element
    cache_mode=CacheMode.BYPASS
)
```

### Session-Based Crawling (Multi-Page)

```python
async def crawl_paginated(start_url):
    async with AsyncWebCrawler() as crawler:
        session_id = "pagination_session"
        all_items = []

        js_next = "document.querySelector('.next-page').click();"

        for page in range(5):
            config = CrawlerRunConfig(
                session_id=session_id,
                js_code=js_next if page > 0 else None,
                css_selector=".item",
                cache_mode=CacheMode.BYPASS
            )
            result = await crawler.arun(start_url, config=config)
            all_items.extend(json.loads(result.extracted_content))

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
        return all_items
```

## Multi-URL Crawling

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

urls = ["https://site1.com", "https://site2.com", "https://site3.com"]

async with AsyncWebCrawler() as crawler:
    results = await crawler.arun_many(urls, config=CrawlerRunConfig())
    for result in results:
        print(f"{result.url}: {len(result.markdown.raw_markdown)} chars")
```

## Adaptive Crawling (Auto-Stop)

```python
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler

async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler)
    result = await adaptive.digest(
        start_url="https://docs.example.com",
        query="authentication API reference"
    )
    adaptive.print_stats()
    print(f"Confidence: {adaptive.confidence:.0%}")
```

## CrawlResult Fields

After `arun()`, access these fields:

- `result.url` - Final URL (after redirects)
- `result.html` - Raw HTML
- `result.cleaned_html` - Sanitized HTML
- `result.markdown.raw_markdown` - Converted Markdown
- `result.markdown.fit_markdown` - Filtered Markdown
- `result.extracted_content` - JSON string (if extraction strategy used)
- `result.links` - Discovered links
- `result.media` - Images, videos, audio
- `result.screenshot` - Base64 screenshot (if requested)
- `result.pdf` - PDF bytes (if requested)

## Additional Resources

- **Extraction strategies details**: See [references/extraction-strategies.md](references/extraction-strategies.md)
- **Browser & crawler config**: See [references/configuration.md](references/configuration.md)
- **Hooks & authentication**: See [references/hooks-auth.md](references/hooks-auth.md)
