# Hooks & Authentication Reference

## Table of Contents
1. [Available Hooks](#available-hooks)
2. [Hook Implementation](#hook-implementation)
3. [Authentication Patterns](#authentication-patterns)
4. [Session Management](#session-management)
5. [Identity-Based Crawling](#identity-based-crawling)

---

## Available Hooks

Hooks execute at specific points in the crawl lifecycle:

| Hook | Trigger Point | Use Case |
|------|--------------|----------|
| `on_browser_created` | Browser instance created | Minimal setup |
| `on_page_context_created` | Page + context ready | Auth, route filtering, viewport |
| `before_goto` | Before navigation | Add headers, modify URL |
| `after_goto` | After page loads | Wait for elements, initial JS |
| `on_execution_started` | Before JS execution | Pre-execution setup |
| `before_retrieve_html` | Before HTML extraction | Final scrolling, cleanup |
| `before_return_html` | Before returning HTML | Last-minute modifications |

---

## Hook Implementation

### Basic Hook Structure

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from playwright.async_api import Page, BrowserContext

async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # Define hooks
        async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
            """Called when page and context are ready"""
            # Block images for faster crawling
            await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda r: r.abort())
            # Set viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            return page

        async def before_goto(page: Page, context: BrowserContext, url: str, **kwargs):
            """Called before navigating to URL"""
            await page.set_extra_http_headers({"X-Custom-Header": "value"})
            return page

        async def after_goto(page: Page, context: BrowserContext, url: str, **kwargs):
            """Called after page loads"""
            await page.wait_for_selector(".content", timeout=5000)
            return page

        async def before_retrieve_html(page: Page, context: BrowserContext, **kwargs):
            """Called before extracting HTML"""
            # Scroll to load lazy content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            return page

        # Register hooks
        crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)
        crawler.crawler_strategy.set_hook("before_goto", before_goto)
        crawler.crawler_strategy.set_hook("after_goto", after_goto)
        crawler.crawler_strategy.set_hook("before_retrieve_html", before_retrieve_html)

        # Run crawl
        result = await crawler.arun("https://example.com")
```

### Route Filtering (Block Resources)

```python
async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
    async def route_handler(route):
        if route.request.resource_type in ["image", "media", "font"]:
            await route.abort()
        elif "analytics" in route.request.url or "tracking" in route.request.url:
            await route.abort()
        else:
            await route.continue_()

    await context.route("**/*", route_handler)
    return page
```

---

## Authentication Patterns

### Cookie-Based Auth

```python
async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
    await context.add_cookies([
        {
            "name": "session_id",
            "value": "your-session-token",
            "domain": ".example.com",
            "path": "/"
        },
        {
            "name": "auth_token",
            "value": "bearer-token",
            "domain": ".example.com",
            "path": "/"
        }
    ])
    return page
```

### Form Login

```python
async def login_and_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "auth_session"

        # Step 1: Navigate to login page and authenticate
        login_js = """
        (async () => {
            document.querySelector('#email').value = 'user@example.com';
            document.querySelector('#password').value = 'password123';
            document.querySelector('#login-form').submit();
        })();
        """

        login_config = CrawlerRunConfig(
            session_id=session_id,
            js_code=login_js,
            wait_for="css:.dashboard",  # Wait for dashboard to confirm login
            cache_mode=CacheMode.BYPASS
        )

        await crawler.arun("https://example.com/login", config=login_config)

        # Step 2: Crawl authenticated pages using same session
        crawl_config = CrawlerRunConfig(
            session_id=session_id,  # Reuse authenticated session
            css_selector=".user-data"
        )

        result = await crawler.arun("https://example.com/protected", config=crawl_config)

        # Clean up
        await crawler.crawler_strategy.kill_session(session_id)

        return result
```

### OAuth / Token Auth

```python
async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
    # Set Authorization header for all requests
    await page.set_extra_http_headers({
        "Authorization": "Bearer your-oauth-token"
    })
    return page
```

### Local Storage Auth

```python
async def after_goto(page: Page, context: BrowserContext, url: str, **kwargs):
    # Set localStorage tokens after page loads
    await page.evaluate("""
        localStorage.setItem('authToken', 'your-token');
        localStorage.setItem('refreshToken', 'your-refresh-token');
    """)
    # Reload to apply auth
    await page.reload()
    await page.wait_for_selector(".authenticated-content")
    return page
```

---

## Session Management

Sessions preserve browser state across multiple `arun()` calls.

### Basic Session Flow

```python
async def session_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "my_session"

        # First request - establishes session
        config1 = CrawlerRunConfig(
            session_id=session_id,
            cache_mode=CacheMode.BYPASS
        )
        result1 = await crawler.arun("https://example.com/page1", config=config1)

        # Second request - reuses same browser tab
        config2 = CrawlerRunConfig(
            session_id=session_id,
            js_code="document.querySelector('.next').click();",
            wait_for="css:.page2-content"
        )
        result2 = await crawler.arun("https://example.com/page1", config=config2)

        # IMPORTANT: Clean up session when done
        await crawler.crawler_strategy.kill_session(session_id)
```

### Pagination with Session

```python
async def crawl_all_pages(start_url, max_pages=10):
    async with AsyncWebCrawler() as crawler:
        session_id = "pagination"
        all_data = []

        js_next_page = """
        const nextBtn = document.querySelector('.pagination .next:not(.disabled)');
        if (nextBtn) nextBtn.click();
        """

        for page_num in range(max_pages):
            config = CrawlerRunConfig(
                session_id=session_id,
                js_code=js_next_page if page_num > 0 else None,
                wait_for="css:.items-loaded",
                js_only=page_num > 0,  # Skip navigation after first page
                extraction_strategy=JsonCssExtractionStrategy(schema),
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(start_url, config=config)

            if result.extracted_content:
                items = json.loads(result.extracted_content)
                if not items:
                    break  # No more items
                all_data.extend(items)

        await crawler.crawler_strategy.kill_session(session_id)
        return all_data
```

### Infinite Scroll

```python
async def crawl_infinite_scroll(url, scroll_count=5):
    async with AsyncWebCrawler() as crawler:
        session_id = "infinite_scroll"

        scroll_js = """
        (async () => {
            const previousHeight = document.body.scrollHeight;
            window.scrollTo(0, document.body.scrollHeight);

            // Wait for new content
            await new Promise(resolve => {
                const checkHeight = setInterval(() => {
                    if (document.body.scrollHeight > previousHeight) {
                        clearInterval(checkHeight);
                        resolve();
                    }
                }, 100);
                setTimeout(() => { clearInterval(checkHeight); resolve(); }, 3000);
            });
        })();
        """

        for i in range(scroll_count):
            config = CrawlerRunConfig(
                session_id=session_id,
                js_code=scroll_js if i > 0 else None,
                js_only=i > 0,
                delay_before_return_html=1.0,
                cache_mode=CacheMode.BYPASS
            )
            await crawler.arun(url, config=config)

        # Final extraction
        final_config = CrawlerRunConfig(
            session_id=session_id,
            extraction_strategy=JsonCssExtractionStrategy(schema)
        )
        result = await crawler.arun(url, config=final_config)

        await crawler.crawler_strategy.kill_session(session_id)
        return result
```

---

## Identity-Based Crawling

For robust authentication, use persistent browser profiles.

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Create persistent profile
browser_config = BrowserConfig(
    headless=False,  # Visible for initial login
    use_persistent_context=True,
    user_data_dir="/path/to/browser/profile"
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    # First run: manually log in (browser is visible)
    # Cookies/localStorage are saved to user_data_dir

    # Subsequent runs: use saved auth state
    result = await crawler.arun("https://example.com/protected")
```

### Save and Restore Storage State

```python
async def save_auth_state():
    async with AsyncWebCrawler() as crawler:
        # Login flow...

        async def save_state(page, context, **kwargs):
            state = await context.storage_state()
            with open("auth_state.json", "w") as f:
                json.dump(state, f)
            return page

        crawler.crawler_strategy.set_hook("before_return_html", save_state)
        await crawler.arun("https://example.com/login", config=login_config)

async def use_saved_auth():
    browser_config = BrowserConfig(
        storage_state="auth_state.json"  # Load saved state
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://example.com/protected")
```

---

## Important Warnings

1. **Don't manipulate pages in wrong hooks** - Creating/closing pages in `on_browser_created` will crash the pipeline

2. **Use `on_page_context_created` for auth** - This is the right hook for login, cookies, route filtering

3. **Always clean up sessions** - Call `kill_session(session_id)` when done to free resources

4. **Hooks can slow down crawling** - Keep them concise and efficient

5. **Handle errors in hooks** - Wrap hook code in try/catch to prevent crawl failures
