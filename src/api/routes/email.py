import logging
from fastapi import APIRouter

from cv_agent.mcp.g_email import (
    EmailResponse,
    InterviewSchedulingResult,
    mcp_send_email,
    schedule_interview_agent,
)
from services.email.schemas import ScheduleInterviewRequest, SendEmailRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email")


@router.post("/follow-up", response_model=InterviewSchedulingResult)
async def get_follow_up_email(
    request: ScheduleInterviewRequest,
) -> InterviewSchedulingResult:
    result = await schedule_interview_agent(
        recruiter_email=request.recruiter_email,
        candidate_email=request.candidate_email,
        candidate_name=request.candidate_name,
        job_title=request.job_title,
    )

    return result


@router.post("", response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
) -> EmailResponse:
    result = await mcp_send_email(
        recruiter_email=request.recruiter_email,
        to=request.to,
        subject=request.subject,
        body=request.body,
    )

    return result
