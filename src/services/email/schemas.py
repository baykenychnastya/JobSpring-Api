from pydantic import BaseModel, EmailStr, Field


class ScheduleInterviewRequest(BaseModel):
    """Request model for scheduling an interview"""

    recruiter_email: EmailStr = Field(..., description="Email address of the recruiter")
    candidate_email: EmailStr = Field(..., description="Email address of the candidate")
    candidate_name: str = Field(
        ..., min_length=1, max_length=100, description="Full name of the candidate"
    )
    job_title: str = Field(
        ..., min_length=1, max_length=200, description="Job title for the interview"
    )


class SendEmailRequest(BaseModel):
    recruiter_email: EmailStr = Field(
        ..., description="Email address of the recruiter sending the message"
    )
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, description="Email subject line")
    body: str = Field(..., min_length=1, description="Email body content")
