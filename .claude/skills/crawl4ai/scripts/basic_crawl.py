#!/usr/bin/env python3
"""
Basic Crawl4AI example - Crawl a URL and extract content as Markdown.

Usage:
    python basic_crawl.py https://example.com
    python basic_crawl.py https://example.com --output result.md
"""

import asyncio
import argparse
import sys
from pathlib import Path

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai import DefaultMarkdownGenerator, PruningContentFilter
except ImportError:
    print("Error: crawl4ai not installed. Run: pip install crawl4ai && crawl4ai-setup")
    sys.exit(1)


async def crawl_url(url: str, output_path: str = None, use_filter: bool = True):
    """
    Crawl a URL and return/save the markdown content.

    Args:
        url: The URL to crawl
        output_path: Optional path to save the markdown output
        use_filter: Whether to use content filtering (removes noise)

    Returns:
        The markdown content
    """
    browser_config = BrowserConfig(headless=True, verbose=False)

    # Configure markdown generation with optional filtering
    markdown_generator = None
    if use_filter:
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.4)
        )

    run_config = CrawlerRunConfig(
        markdown_generator=markdown_generator,
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
        excluded_tags=["nav", "footer", "header", "aside", "script", "style"],
        remove_overlay_elements=True,
    )

    print(f"Crawling: {url}")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url, config=run_config)

        if not result.success:
            print(f"Error: Crawl failed - {result.error_message}")
            return None

        # Get the appropriate markdown content
        if use_filter and result.markdown.fit_markdown:
            content = result.markdown.fit_markdown
        else:
            content = result.markdown.raw_markdown

        print(f"Success! Extracted {len(content)} characters")

        # Save if output path provided
        if output_path:
            Path(output_path).write_text(content, encoding="utf-8")
            print(f"Saved to: {output_path}")

        return content


def main():
    parser = argparse.ArgumentParser(
        description="Crawl a URL and extract markdown content"
    )
    parser.add_argument("url", help="The URL to crawl")
    parser.add_argument("-o", "--output", help="Output file path for markdown")
    parser.add_argument(
        "--no-filter", action="store_true", help="Disable content filtering"
    )

    args = parser.parse_args()

    content = asyncio.run(
        crawl_url(url=args.url, output_path=args.output, use_filter=not args.no_filter)
    )

    if content and not args.output:
        print("\n" + "=" * 50 + "\n")
        print(content[:2000])
        if len(content) > 2000:
            print(f"\n... [truncated, {len(content)} total characters]")


if __name__ == "__main__":
    main()
