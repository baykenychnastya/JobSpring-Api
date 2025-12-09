from typing import List, Optional
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """Represents a single calendar event."""

    summary: str = Field(description="Event title/summary")
    start_time: str = Field(description="Event start time in ISO format")
    end_time: str = Field(description="Event end time in ISO format")
    location: Optional[str] = Field(default=None, description="Event location")
    attendees: Optional[List[str]] = Field(
        default=None, description="List of attendee emails"
    )
    event_id: str = Field(description="Unique event identifier")
    link: Optional[str] = Field(default=None, description="Link to the event")


class CalendarEventsResponse(BaseModel):
    """Response containing calendar events."""

    events: List[CalendarEvent] = Field(description="List of calendar events")


class ScheduleInterviewResponse(BaseModel):
    event_id: str
    event_link: str
    summary: str
    start_time: str
    end_time: str
    attendees: list[str]
    google_meet_link: str | None = None
    success: bool
    message: str | None = None
