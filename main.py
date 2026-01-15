import asyncio
from datetime import datetime
from pathlib import Path

from crawlers.facebook import crawl_facebook_events
from models.event import Event

OUTPUT_DIR = Path("outputs")


def generate_markdown(events: list[Event], source_url: str) -> None:
    """Generate markdown file from extracted events."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "events.md"

    header = f"""# Événements

> Généré le {datetime.now().strftime("%Y-%m-%d %H:%M")}
> Source: {source_url}

---

"""

    events_md = ""
    for event in events:
        events_md += f"""## {event.title}
- **Date:** {event.date}
- **Organisateur:** {event.organizer}
- **Lien:** {event.link}

"""

    content = header + events_md
    output_path.write_text(content, encoding="utf-8")
    print(f"Markdown saved to {output_path}")


async def main() -> None:
    """Main entry point."""
    page_name = "BrasserieOrville"
    source_url = f"https://www.facebook.com/{page_name}/events"

    print(f"Crawling {page_name} events...")
    events = await crawl_facebook_events(page_name)

    if not events:
        print("No events found.")
        return

    print(f"Found {len(events)} events.")
    generate_markdown(events, source_url)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
