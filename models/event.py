from pydantic import BaseModel


class Event(BaseModel):
    """Event data model."""

    date: str
    title: str
    organizer: str
    link: str
