import logging
from fastapi import APIRouter, HTTPException

from cv_agent.mcp.availability_checker import RecruiterAvailabilityChecker
from cv_agent.mcp.g_calendar import get_calendar_events, schedule_interview
from cv_agent.mcp.schemas import CalendarEventsResponse, ScheduleInterviewResponse
from services.calendar.schemas import (
    GetAvailableSlotResponse,
    GetAvailableSlots,
    GetCalendarEvents,
    ScheduleInterviewRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar")


@router.get("/events", response_model=CalendarEventsResponse)
async def get_events(request: GetCalendarEvents) -> CalendarEventsResponse:
    """
    Get calendar events for a user within a specified time range.

    Args:
        request: GetCalendarEvents request containing user_email, start_time, and end_time

    Returns:
        CalendarEventsResponse with the list of calendar events

    Raises:
        HTTPException: If there's an error fetching the events
    """
    try:
        result = await get_calendar_events(
            user_email=request.user_email,
            start_time=request.start_time,
            end_time=request.end_time,
        )
        return result

    except Exception as e:
        logger.error(
            f"Error fetching calendar events for {request.user_email}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch calendar events: {str(e)}"
        )


@router.post("/available-slots", response_model=GetAvailableSlotResponse)
async def get_available_slots(request: GetAvailableSlots) -> GetAvailableSlotResponse:
    try:
        availability_checker = RecruiterAvailabilityChecker()
        result = await availability_checker.get_available_slots_str(request.user_email)
        return GetAvailableSlotResponse(available_slots=result)

    except Exception as e:
        logger.error(
            f"Error fetching available slots for {request.user_email}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch available slots: {str(e)}"
        )


@router.post("/schedule-interview", response_model=ScheduleInterviewResponse)
async def schedule_interview_endpoint(
    request: ScheduleInterviewRequest,
) -> ScheduleInterviewResponse:
    """
    Schedule an interview on Google Calendar.

    Args:
        request: ScheduleInterviewRequest containing interview details

    Returns:
        ScheduleInterviewResponse with the created event details

    Raises:
        HTTPException: If there's an error scheduling the interview
    """
    try:
        logger.info(
            f"Scheduling interview for candidate {request.candidate_name} "
            f"with organizer {request.user_email}"
        )

        result = await schedule_interview(
            user_email=request.user_email,
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            position=request.position,
            start_time=request.start_time,
            end_time=request.end_time,
            timezone=request.timezone,
            location=request.location,
            interviewer_emails=request.interviewer_emails,
            add_google_meet=request.add_google_meet,
            description=request.description,
        )

        if not result.success:
            logger.error(
                f"Failed to schedule interview for {request.candidate_name}: "
                f"{result.message}"
            )
            raise HTTPException(
                status_code=400,
                detail=result.message or "Failed to schedule interview",
            )

        logger.info(
            f"Successfully scheduled interview. Event ID: {result.event_id}, "
            f"Link: {result.event_link}"
        )

        return result

    except Exception as e:
        logger.error(
            f"Error scheduling interview for {request.candidate_name}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to schedule interview: {str(e)}"
        )
