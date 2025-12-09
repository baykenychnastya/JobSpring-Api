from datetime import datetime
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent

from cv_agent.mcp.schemas import CalendarEventsResponse, ScheduleInterviewResponse
from cv_agent.mcp.config import google_workspace_mcp_settings


async def get_calendar_events(
    user_email: str,
    start_time: datetime,
    end_time: datetime,
) -> CalendarEventsResponse:
    """
    Fetch calendar events for a user within a specified time range.

    Args:
        user_email: The user's Google email address
        start_time: Start of the time range
        end_time: End of the time range

    Returns:
        CalendarEventsResponse with the events data
    """
    async with streamablehttp_client(str(google_workspace_mcp_settings.url)) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            llm = ChatGoogleGenerativeAI(
                model=google_workspace_mcp_settings.llm_model,
                temperature=google_workspace_mcp_settings.llm_temperature,
            )

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

            system_prompt = f"""You are a helpful assistant to manage calendar events for {user_email}. 
Today's date and time is {now_str}.

When retrieving calendar events:
1. Use the get_events tool with the user's email
2. Extract all relevant event information
3. Return a structured response with all events found"""

            agent = create_agent(
                llm,
                tools,
                response_format=CalendarEventsResponse,
                system_prompt=system_prompt,
            )

            user_message = f"""Get all calendar events for {user_email} between {start_str} and {end_str}.
            
Return the results in the following structured format:
- events: list of all events with their details (summary, start_time, end_time, location, attendees, event_id, link)
"""

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_message)]}
            )

            return result["structured_response"]


async def schedule_interview(
    user_email: str,
    candidate_name: str,
    candidate_email: str,
    position: str,
    start_time: datetime,
    end_time: datetime,
    timezone: str = "UTC",
    location: str | None = None,
    interviewer_emails: list[str] | None = None,
    add_google_meet: bool = True,
    description: str | None = None,
) -> ScheduleInterviewResponse:
    """
    Schedule an interview event on Google Calendar.

    Args:
        user_email: The user's Google email address (organizer)
        candidate_name: Name of the candidate being interviewed
        candidate_email: Email of the candidate
        position: Position/role for the interview
        start_time: Interview start time
        end_time: Interview end time
        timezone: Timezone for the event (default: UTC)
        location: Physical location (optional if using Google Meet)
        interviewer_emails: List of additional interviewer emails
        add_google_meet: Whether to add Google Meet link (default: True)
        description: Additional description for the interview

    Returns:
        ScheduleInterviewResponse with the created event details
    """
    async with streamablehttp_client(str(google_workspace_mcp_settings.url)) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            llm = ChatGoogleGenerativeAI(
                model=google_workspace_mcp_settings.llm_model,
                temperature=google_workspace_mcp_settings.llm_temperature,
            )

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

            attendees = [candidate_email]
            if interviewer_emails:
                attendees.extend(interviewer_emails)

            interview_description = (
                f"Interview for position: {position}\nCandidate: {candidate_name}"
            )
            if description:
                interview_description += f"\n\n{description}"

            system_prompt = f"""You are a helpful assistant to schedule calendar events for {user_email}. 
Today's date and time is {now_str}.

When creating interview events:
1. Use the create_event tool with all provided details
2. Ensure all attendees are included
3. Add Google Meet if requested
4. Return a structured response with the created event details"""

            agent = create_agent(
                llm,
                tools,
                response_format=ScheduleInterviewResponse,
                system_prompt=system_prompt,
            )

            user_message = f"""Schedule an interview event with the following details:
- Summary: Interview - {candidate_name} for {position}
- Start time: {start_str}
- End time: {end_str}
- Timezone: {timezone}
- Description: {interview_description}
- Attendees: {", ".join(attendees)}
- Add Google Meet: {add_google_meet}
"""

            if location:
                user_message += f"- Location: {location}\n"

            user_message += """
Return the results in the following structured format:
- event_id: the created event ID
- event_link: link to the calendar event
- summary: event title
- start_time: event start time
- end_time: event end time
- attendees: list of attendee emails
- google_meet_link: Google Meet link (if added)
- success: whether the event was created successfully
- message: any relevant message or error
"""

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_message)]}
            )

            return result["structured_response"]
