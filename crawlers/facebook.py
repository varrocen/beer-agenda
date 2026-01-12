import json

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from extractors.events import get_extraction_strategy
from models.event import Event


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
    # Script to dismiss popups (cookies + login)
    dismiss_popups_js = """
    (async () => {
        // Wait for page to load
        await new Promise(r => setTimeout(r, 2000));

        // Dismiss cookie popup
        const buttons = [...document.querySelectorAll('div[role="button"], span, button')];
        const declineBtn = buttons.find(b => b.textContent.includes('Decline optional cookies'));
        if (declineBtn) declineBtn.click();

        // Wait and scroll to trigger login popup
        await new Promise(r => setTimeout(r, 1000));
        window.scrollTo(0, document.body.scrollHeight);

        // Wait for login popup and close it
        await new Promise(r => setTimeout(r, 2000));
        const closeBtn = document.querySelector('[aria-label="Close"]');
        if (closeBtn) closeBtn.click();

        // Scroll again to load more content
        await new Promise(r => setTimeout(r, 1000));
        window.scrollTo(0, document.body.scrollHeight);
    })();
    """
    return CrawlerRunConfig(
        simulate_user=True,
        mean_delay=3.0,
        delay_before_return_html=12.0,
        scroll_delay=1.0,
        js_code=dismiss_popups_js,
        extraction_strategy=get_extraction_strategy(),
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
