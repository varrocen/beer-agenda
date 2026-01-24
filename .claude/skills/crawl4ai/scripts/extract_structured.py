#!/usr/bin/env python3
"""
Structured data extraction with Crawl4AI using CSS selectors.

This example demonstrates how to extract structured JSON data from web pages
without using LLMs - fast, reliable, and cost-free.

Usage:
    python extract_structured.py
"""

import asyncio
import json
import sys

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai import JsonCssExtractionStrategy
except ImportError:
    print("Error: crawl4ai not installed. Run: pip install crawl4ai && crawl4ai-setup")
    sys.exit(1)


# Example schemas for common use cases

HACKER_NEWS_SCHEMA = {
    "name": "HackerNewsItems",
    "baseSelector": "tr.athing",
    "fields": [
        {"name": "rank", "selector": "span.rank", "type": "text"},
        {"name": "title", "selector": "span.titleline > a", "type": "text"},
        {
            "name": "url",
            "selector": "span.titleline > a",
            "type": "attribute",
            "attribute": "href",
        },
        {
            "name": "site",
            "selector": "span.sitestr",
            "type": "text",
            "default": "news.ycombinator.com",
        },
    ],
}

PRODUCT_SCHEMA = {
    "name": "Products",
    "baseSelector": ".product-card, .product-item, [data-product]",
    "fields": [
        {"name": "name", "selector": "h2, h3, .product-name, .title", "type": "text"},
        {
            "name": "price",
            "selector": ".price, .product-price, [data-price]",
            "type": "text",
        },
        {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"},
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
        {
            "name": "description",
            "selector": ".description, .product-desc, p",
            "type": "text",
            "default": "",
        },
    ],
}

ARTICLE_SCHEMA = {
    "name": "Articles",
    "baseSelector": "article, .article, .post, .entry",
    "fields": [
        {"name": "title", "selector": "h1, h2, .title, .headline", "type": "text"},
        {
            "name": "author",
            "selector": ".author, .byline, [rel='author']",
            "type": "text",
            "default": "Unknown",
        },
        {
            "name": "date",
            "selector": "time, .date, .published",
            "type": "text",
            "default": "",
        },
        {
            "name": "summary",
            "selector": ".excerpt, .summary, .lead, p:first-of-type",
            "type": "text",
        },
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
    ],
}


async def extract_with_schema(url: str, schema: dict, verbose: bool = True):
    """
    Extract structured data from a URL using a CSS schema.

    Args:
        url: The URL to crawl
        schema: The extraction schema
        verbose: Print progress messages

    Returns:
        List of extracted items
    """
    strategy = JsonCssExtractionStrategy(schema, verbose=verbose)

    config = CrawlerRunConfig(
        extraction_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        excluded_tags=["nav", "footer", "header"],
    )

    if verbose:
        print(f"Extracting from: {url}")
        print(f"Using schema: {schema['name']}")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config)

        if not result.success:
            print(f"Error: {result.error_message}")
            return []

        if result.extracted_content:
            items = json.loads(result.extracted_content)
            if verbose:
                print(f"Extracted {len(items)} items")
            return items

        return []


async def demo_hacker_news():
    """Demo: Extract Hacker News front page stories."""
    print("\n" + "=" * 60)
    print("Demo: Hacker News Front Page")
    print("=" * 60)

    items = await extract_with_schema(
        "https://news.ycombinator.com", HACKER_NEWS_SCHEMA
    )

    for item in items[:5]:
        print(f"\n{item.get('rank', '?')}. {item.get('title', 'No title')}")
        print(f"   URL: {item.get('url', 'N/A')}")
        print(f"   Site: {item.get('site', 'N/A')}")


async def demo_custom_schema():
    """Demo: Create and use a custom schema."""
    print("\n" + "=" * 60)
    print("Demo: Custom Schema for GitHub Trending")
    print("=" * 60)

    github_trending_schema = {
        "name": "TrendingRepos",
        "baseSelector": "article.Box-row",
        "fields": [
            {"name": "name", "selector": "h2 a", "type": "text", "transform": "strip"},
            {
                "name": "url",
                "selector": "h2 a",
                "type": "attribute",
                "attribute": "href",
            },
            {
                "name": "description",
                "selector": "p",
                "type": "text",
                "default": "No description",
            },
            {
                "name": "language",
                "selector": "[itemprop='programmingLanguage']",
                "type": "text",
                "default": "Unknown",
            },
            {
                "name": "stars",
                "selector": "a[href*='/stargazers']",
                "type": "text",
                "transform": "strip",
            },
        ],
    }

    items = await extract_with_schema(
        "https://github.com/trending", github_trending_schema
    )

    for item in items[:5]:
        print(f"\n📦 {item.get('name', 'Unknown')}")
        print(f"   {item.get('description', 'No description')[:60]}...")
        print(f"   ⭐ {item.get('stars', '?')} | 💻 {item.get('language', 'Unknown')}")


def create_schema_template(name: str, base_selector: str, fields: list) -> dict:
    """
    Helper to create extraction schemas.

    Args:
        name: Schema identifier
        base_selector: CSS selector for each item container
        fields: List of (name, selector, type) tuples

    Returns:
        Schema dictionary
    """
    return {
        "name": name,
        "baseSelector": base_selector,
        "fields": [
            {"name": f[0], "selector": f[1], "type": f[2] if len(f) > 2 else "text"}
            for f in fields
        ],
    }


async def main():
    print("Crawl4AI Structured Extraction Demo")
    print("=" * 60)

    await demo_hacker_news()
    await demo_custom_schema()

    print("\n" + "=" * 60)
    print("Available pre-built schemas:")
    print("  - HACKER_NEWS_SCHEMA")
    print("  - PRODUCT_SCHEMA")
    print("  - ARTICLE_SCHEMA")
    print("\nTo use: items = await extract_with_schema(url, SCHEMA)")


if __name__ == "__main__":
    asyncio.run(main())
