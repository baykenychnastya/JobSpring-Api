import logging
from datetime import datetime
from typing import Literal, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp import ClientSession
from langchain.agents import create_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.client.streamable_http import streamablehttp_client
from cv_agent.mcp.availability_checker import AvailabilityConstraints
from cv_agent.mcp.config import google_workspace_mcp_settings

logger = logging.getLogger(__name__)

load_dotenv()


class EmailResponse(BaseModel):
    status: Literal["success", "error"] = Field(
        ..., description="Status of the email operation"
    )
    message: str = Field(..., description="Human-readable message about the operation")
    from_email: EmailStr = Field(..., description="Sender email address")
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")


class NextEmail(BaseModel):
    """Next email to send in the conversation"""

    subject: str = Field(description="Email subject line")
    body: str = Field(
        description="Email body content with specific time slots if proposing interview times"
    )


class InterviewSchedulingResult(BaseModel):
    """Result of email analysis for interview scheduling"""

    interview_preparation_status: Literal["IN_PROGRESS", "DONE"] = Field(
        description="Status of interview scheduling process"
    )
    schedule_start_time: Optional[datetime] = Field(
        default=None,
        description="Scheduled interview start time in ISO format (only when DONE)",
    )
    next_email: Optional[NextEmail] = Field(
        default=None, description="Next email to send (only when IN_PROGRESS)"
    )
    reasoning: str = Field(
        description="Detailed explanation of the decision and actions taken"
    )


def format_constraints_for_prompt(constraints: AvailabilityConstraints) -> str:
    """Format availability constraints for the system prompt"""
    return f"""
RECRUITER AVAILABILITY CONSTRAINTS:
- Working Hours: {constraints.earliest_meeting_time.strftime("%I:%M %p")} - {constraints.latest_meeting_end.strftime("%I:%M %p")}
- Lunch Break: {constraints.lunch_break_start.strftime("%I:%M %p")} - {constraints.lunch_break_end.strftime("%I:%M %p")}
- Meeting Duration: {constraints.meeting_duration_minutes} minutes
- Minimum Break Between Meetings: {constraints.min_break_between_meetings} minutes
- Maximum Meetings Per Day: {constraints.max_meetings_per_day}
- Setup Time Before Meeting: {constraints.setup_time_minutes} minutes
"""


async def schedule_interview_agent(
    recruiter_email: str,
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    constraints: Optional[AvailabilityConstraints] = AvailabilityConstraints(),
) -> InterviewSchedulingResult:
    """
    Agentic interview scheduling that autonomously:
    1. Reads email thread between recruiter and candidate
    2. Checks recruiter's calendar for availability
    3. Determines if interview is scheduled or needs follow-up
    4. Generates appropriate next email with specific time slots

    Args:
        recruiter_email: Recruiter's email address
        candidate_email: Candidate's email address
        candidate_name: Candidate's full name
        job_title: Job position title
        constraints: Optional availability constraints for the recruiter

    Returns:
        InterviewSchedulingResult with status and next action
    """
    if constraints is None:
        constraints = AvailabilityConstraints()

    logger.info(f"Starting interview scheduling agent for {candidate_email}")

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

            constraints_text = format_constraints_for_prompt(constraints)

            system_prompt = f"""You are an intelligent interview scheduling agent working for a recruiter.

    MISSION:
    Analyze the email conversation between the recruiter and candidate, check the recruiter's calendar availability, 
    and determine the next step in scheduling an interview.

    RECRUITER INFORMATION:
    - Recruiter Email: {recruiter_email}
    - Candidate Email: {candidate_email}
    - Candidate Name: {candidate_name}
    - Job Position: {job_title}

    {constraints_text}

    AVAILABLE TOOLS:
    You have access to Google Workspace tools via MCP:
    - Gmail: Read emails, search threads, get message details
    - Google Calendar: Check availability, get free/busy times, list events

    WORKFLOW YOU MUST FOLLOW:

    1. READ EMAIL THREAD
    - Use Gmail tools to find all emails between {recruiter_email} and {candidate_email}
    - Search for emails related to interview scheduling for {job_title}
    - Read the complete conversation thread in chronological order

    2. ANALYZE CONVERSATION STATE
    - Determine if this is first contact (no emails yet)
    - Check if candidate has responded
    - Identify if candidate confirmed a specific date/time
    - Check if candidate asked questions or proposed alternatives
    - Look for explicit confirmation phrases like "Yes, I confirm" or "I'll be there on [date/time]"

    3. CHECK RECRUITER AVAILABILITY (if needed for next email)
    - Use Calendar tools to check {recruiter_email}'s calendar
    - Find available slots in the next 7-14 days
    - Respect all availability constraints (working hours, lunch break, etc.)
    - Find 3-5 suitable time slots that comply with constraints
    - Ensure slots don't conflict with existing meetings

    4. MAKE DECISION
    Status should be "DONE" ONLY when:
    - Candidate has EXPLICITLY confirmed a specific date and time
    - Both parties agreed on the schedule
    - Confirmation is unambiguous (e.g., "Yes, Monday December 2nd at 2 PM works for me")
    
    Status should be "IN_PROGRESS" when:
    - No email thread exists yet (initial outreach needed)
    - Candidate hasn't responded yet
    - Candidate responded but didn't confirm a time
    - Candidate asked questions without committing to a time
    - Candidate proposed alternatives that need confirmation
    - Candidate declined all times and needs new options
    - Any further communication is needed

    5. GENERATE OUTPUT
    If DONE:
    - Extract the confirmed interview datetime
    - Return it in ISO format
    - Include reasoning about what confirmed the meeting
    
    If IN_PROGRESS:
    - Compose a professional email
    - Include specific available time slots from calendar check
    - Address any questions or concerns from candidate
    - Keep it concise and action-oriented
    - Use proper email etiquette

    CRITICAL RULES:
    - ALWAYS use tools to read actual emails - do NOT assume or hallucinate email content
    - Example of valid search query "(from:recruiter@gmail.com to:candidate@gmail.com) OR (from:candidate@gmail.com to:recruiter@gmail.com)"
    - ALWAYS check calendar for actual availability - do NOT propose fake time slots
    - Only mark as DONE with explicit candidate confirmation
    - When proposing times, include date, day of week, time, and timezone
    - Be professional, warm, and concise in email generation
    - If tools fail, explain what failed in the reasoning

    EXAMPLE TIME SLOT FORMAT:
    "Here are some available times for our interview:
    - Monday, December 2, 2025 at 2:00 PM EST
    - Tuesday, December 3, 2025 at 10:30 AM EST  
    - Wednesday, December 4, 2025 at 3:00 PM EST"

    Now, execute the workflow and provide your structured output."""

            agent = create_agent(
                llm,
                tools,
                response_format=InterviewSchedulingResult,
                system_prompt=system_prompt,
            )

            user_prompt = f"""Execute the interview scheduling workflow for:
    - Recruiter: {recruiter_email}
    - Candidate: {candidate_email} ({candidate_name})
    - Position: {job_title}

    Follow the workflow step by step:
    1. Read the email thread between recruiter and candidate
    2. Analyze the conversation state
    3. Check recruiter's calendar availability if needed
    4. Decide: DONE or IN_PROGRESS
    5. Generate the appropriate output

    Use the available tools to gather all necessary information before making your decision."""

            try:
                response = await agent.ainvoke(
                    {
                        "messages": [
                            HumanMessage(content=user_prompt),
                        ]
                    }
                )

                result = response["structured_response"]

                # Validation
                if result.interview_preparation_status == "DONE":
                    if not result.schedule_start_time:
                        logger.error(
                            "Status is DONE but no schedule_start_time provided"
                        )
                        raise ValueError("DONE status requires schedule_start_time")
                    if result.next_email:
                        logger.warning(
                            "Status is DONE but next_email provided, removing it"
                        )
                        result.next_email = None
                    logger.info(
                        f"Interview scheduled for: {result.schedule_start_time}"
                    )

                elif result.interview_preparation_status == "IN_PROGRESS":
                    if not result.next_email:
                        logger.error("Status is IN_PROGRESS but no next_email provided")
                        raise ValueError("IN_PROGRESS status requires next_email")
                    if result.schedule_start_time:
                        logger.warning(
                            "Status is IN_PROGRESS but schedule_start_time provided, removing it"
                        )
                        result.schedule_start_time = None
                    logger.info(f"Next email prepared: {result.next_email.subject}")

                logger.info(f"Agent completed: {result.interview_preparation_status}")
                return result

            except Exception as e:
                logger.error(f"Error in scheduling agent: {e}", exc_info=True)

                # Fallback: return a safe default
                return InterviewSchedulingResult(
                    interview_preparation_status="IN_PROGRESS",
                    next_email=NextEmail(
                        subject=f"Interview Opportunity - {job_title}",
                        body=f"""Dear {candidate_name},

    Thank you for your interest in the {job_title} position. We would like to schedule an interview with you.

    Please let me know your availability for a {constraints.meeting_duration_minutes}-minute conversation in the coming week, and I'll find a suitable time in my calendar.

    Best regards,
    {recruiter_email.split("@")[0].title()}""",
                    ),
                    reasoning=f"Agent error occurred: {str(e)}. Defaulting to initial outreach email.",
                )


async def mcp_send_email(
    recruiter_email: str,
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    body_format: Literal["plain", "html"] = "plain",
) -> EmailResponse:
    """
    Send an email using the recruiter's Gmail account via MCP.
    Automatically replies in existing thread if one exists.

    Args:
        recruiter_email: Sender's email address (recruiter)
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        cc: Optional CC email address
        bcc: Optional BCC email address
        body_format: Email body format ('plain' or 'html')

    Returns:
        dict with status and message_id or error information
    """
    logger.info(f"Sending email from {recruiter_email} to {to}")

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
                temperature=0,  # Use 0 for deterministic email sending
            )

            system_prompt = f"""You are an email sending assistant.

MISSION:
Send an email using Gmail on behalf of the recruiter. If an existing email thread exists between the sender and recipient, reply within that thread. Otherwise, send a new email.

SENDER INFORMATION:
- Sender Email: {recruiter_email}
- Recipient Email: {to}
- Subject: {subject}
- Body Format: {body_format}

WORKFLOW YOU MUST FOLLOW:

1. CHECK FOR EXISTING THREAD
- Use search_gmail_messages to find any existing email conversation between {recruiter_email} and {to}
- Search query example: "from:{to} OR to:{to}"
- If messages are found, get the thread_id from the most recent message
- Use get_gmail_thread_content to retrieve the full thread details if needed
- Extract thread_id, in_reply_to (Message-ID), and references headers from the most recent message

2. SEND EMAIL
- If an existing thread was found:
  - Use send_gmail_message with thread_id, in_reply_to, and references parameters to reply in the thread
  - This keeps the conversation organized in Gmail
- If no existing thread found:
  - Use send_gmail_message to send a new email without thread parameters

Parameters to use:
- user_google_email: {recruiter_email}
- to: {to}
- subject: {subject}
- body: (the body content provided)
- body_format: {body_format}
- cc: {cc if cc else "None"}
- bcc: {bcc if bcc else "None"}
- thread_id: (if replying to existing thread)
- in_reply_to: (Message-ID from previous email if replying)
- references: (chain of Message-IDs if replying)

3. CONFIRM SUCCESS
- After sending, confirm whether it was sent as a reply or new email
- Return the message ID and thread information

CRITICAL RULES:
- ALWAYS search for existing threads first
- If a thread exists, ALWAYS reply within it using thread_id, in_reply_to, and references
- Use the exact parameters provided
- Do NOT modify the subject or body content
- Report any errors clearly
- If search returns multiple threads, use the most recent one

Now, execute the email sending workflow."""

            agent = create_agent(
                llm,
                tools,
                system_prompt=system_prompt,
            )

            user_prompt = f"""Send the following email, checking first if there's an existing thread to reply to:

From: {recruiter_email}
To: {to}
Subject: {subject}
Body Format: {body_format}
{f"CC: {cc}" if cc else ""}
{f"BCC: {bcc}" if bcc else ""}

Body:
{body}

Step-by-step:
1. Search for existing email threads between {recruiter_email} and {to}
2. If thread exists, extract thread_id, in_reply_to, and references from the most recent message
3. Send the email (as reply if thread exists, or as new email if not)
4. Confirm success

Use the Gmail tools to complete this workflow."""

            try:
                response = await agent.ainvoke(
                    {
                        "messages": [
                            HumanMessage(content=user_prompt),
                        ]
                    }
                )

                # Extract the result from the agent's response
                logger.info("Email sent successfully")

                return EmailResponse(
                    status="success",
                    message="Email sent successfully",
                    from_email=recruiter_email,
                    to=to,
                    subject=subject,
                )

            except Exception as e:
                logger.error(f"Error sending email: {e}", exc_info=True)
                return EmailResponse(
                    status="error",
                    message=f"Failed to send email: {str(e)}",
                    from_email=recruiter_email,
                    to=to,
                    subject=subject,
                )
