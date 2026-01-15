from crawl4ai import LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from models.event import Event

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "ollama/mistral:7b"


def get_facebook_events_extraction_strategy() -> LLMExtractionStrategy:
    """Get LLM extraction strategy for events."""
    llm_config = LLMConfig(
        provider=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    return LLMExtractionStrategy(
        llm_config=llm_config,
        schema=Event.model_json_schema(),
        extraction_type="schema",
        instruction="""Extract all events from this Facebook page.
Each event has:
- date: the date and time (e.g., "Thu, 15 Jan at 17:00 CET")
- title: the event name in brackets (e.g., "[Jeudi Concert]")
- organizer: found after "Event by" (e.g., "Brasserie d'Orville")
- link: the Facebook event URL (e.g., "https://www.facebook.com/events/123456/")
Extract ALL events that have a Facebook event link.""",
        input_format="markdown",
        extra_args={"temperature": 0.0, "num_ctx": 16384},
    )
