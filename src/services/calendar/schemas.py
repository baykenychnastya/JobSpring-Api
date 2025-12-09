from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class GetAvailableSlots(BaseModel):
    user_email: EmailStr = Field(..., description="The user's Google email address")


class GetAvailableSlotResponse(BaseModel):
    available_slots: str


class GetCalendarEvents(BaseModel):
    """Request schema for getting calendar events via API."""

    user_email: EmailStr = Field(..., description="The user's Google email address")
    start_time: datetime = Field(
        ..., description="Start of the time range for fetching events"
    )
    end_time: datetime = Field(
        ..., description="End of the time range for fetching events"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "start_time": "2025-12-01T00:00:00",
                "end_time": "2025-12-31T23:59:59",
            }
        }


class ScheduleInterviewRequest(BaseModel):
    """Request schema for scheduling an interview."""

    user_email: EmailStr = Field(
        ..., description="The organizer's Google email address"
    )
    candidate_name: str = Field(
        ..., description="Name of the candidate being interviewed"
    )
    candidate_email: EmailStr = Field(..., description="Email of the candidate")
    position: str = Field(..., description="Position/role for the interview")
    start_time: datetime = Field(..., description="Interview start time")
    end_time: datetime = Field(..., description="Interview end time")
    timezone: str = Field(default="UTC", description="Timezone for the event")
    location: str | None = Field(None, description="Physical location (optional)")
    interviewer_emails: list[EmailStr] | None = Field(
        None, description="List of additional interviewer emails"
    )
    add_google_meet: bool = Field(True, description="Whether to add Google Meet link")
    description: str | None = Field(
        None, description="Additional description for the interview"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "recruiter@company.com",
                "candidate_name": "John Doe",
                "candidate_email": "john.doe@example.com",
                "position": "Senior Software Engineer",
                "start_time": "2024-12-10T14:00:00",
                "end_time": "2024-12-10T15:00:00",
                "timezone": "America/New_York",
                "location": "Office - Conference Room A",
                "interviewer_emails": [
                    "interviewer1@company.com",
                    "interviewer2@company.com",
                ],
                "add_google_meet": True,
                "description": "Technical interview focusing on system design and coding skills.",
            }
        }
