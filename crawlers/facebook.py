from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


def get_facebook_browser_config() -> BrowserConfig:
    """Get Facebook-specific browser configuration."""
    return BrowserConfig(
        headless=False,
        enable_stealth=True,
        user_agent_mode="random",
        viewport_width=1920,
        viewport_height=1080,
        use_persistent_context=True,
        verbose=False,
    )


def get_facebook_run_config() -> CrawlerRunConfig:
    """Get Facebook-specific run configuration."""
    return CrawlerRunConfig(
        simulate_user=True,
        mean_delay=3.0,
        delay_before_return_html=2.0,
    )


async def crawl_facebook_events(page_name: str) -> str | None:
    """Crawl Facebook events page and return markdown content."""
    url = f"https://www.facebook.com/{page_name}/events"

    browser_config = get_facebook_browser_config()
    run_config = get_facebook_run_config()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            print(f"Crawl failed: {result.error_message}")
            return None

        return result.markdown
