import json
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from extractors.events import get_facebook_events_extraction_strategy
from models.event import Event

SCRIPTS_DIR = Path(__file__).parent / "scripts"


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
    """Get Facebook-specific run configuration with LLM extraction."""
    decline_popups_and_scroll_js = (
        SCRIPTS_DIR / "facebook_decline_popups_and_scroll.js"
    ).read_text()
    return CrawlerRunConfig(
        simulate_user=True,
        mean_delay=3.0,
        delay_before_return_html=12.0,
        scroll_delay=1.0,
        js_code=decline_popups_and_scroll_js,
        extraction_strategy=get_facebook_events_extraction_strategy(),
    )


async def crawl_facebook_events(page_name: str) -> list[Event]:
    """Crawl Facebook events page and extract events."""
    url = f"https://www.facebook.com/{page_name}/events"

    browser_config = get_facebook_browser_config()
    run_config = get_facebook_run_config()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            print(f"Crawl failed: {result.error_message}")
            return []

        # Debug: save raw markdown to see what LLM receives
        if result.markdown:
            debug_path = "outputs/debug_markdown.md"
            with open(debug_path, "w") as f:
                f.write(result.markdown)
            print(f"Debug markdown saved to {debug_path}")

        if not result.extracted_content:
            print("No content extracted.")
            return []

        extracted = json.loads(result.extracted_content)
        return [Event(**item) for item in extracted]
