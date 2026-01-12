import asyncio
from datetime import datetime
from pathlib import Path

from crawlers.facebook import crawl_facebook_events

OUTPUT_DIR = Path("outputs")


def generate_markdown(raw_content: str, source_url: str) -> None:
    """Generate markdown file from crawled content."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "events.md"

    header = f"""# Événements

> Généré le {datetime.now().strftime("%Y-%m-%d %H:%M")}
> Source: {source_url}

---

"""

    content = header + raw_content
    output_path.write_text(content, encoding="utf-8")
    print(f"Markdown saved to {output_path}")


async def main() -> None:
    """Main entry point."""
    page_name = "BrasserieOrville"
    source_url = f"https://www.facebook.com/{page_name}/events"

    print(f"Crawling {page_name} events...")
    content = await crawl_facebook_events(page_name)

    if not content:
        print("Failed to retrieve content.")
        return

    generate_markdown(content, source_url)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
