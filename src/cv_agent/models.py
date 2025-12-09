from pydantic import BaseModel, Field
from typing import List, Literal, TypedDict


class Contact(BaseModel):
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    location: str = ""


class Education(BaseModel):
    degree: str = ""
    field: str = ""
    institution: str = ""
    start_year: str = ""
    end_year: str = ""


class Experience(BaseModel):
    job_title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class Project(BaseModel):
    title: str = ""
    description: str = ""


class ParsedCV(BaseModel):
    full_name: str = ""
    contact: Contact = Field(default_factory=Contact)
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)


class PriorityAnalysisResponse(BaseModel):
    priority: Literal["recommended", "highly-recommended", "not-recommended"] = Field(
        default="not-recommended", description="The priority level of the candidate"
    )
    priority_description: str = Field(
        default="",
        description="2-4 sentences explaining the classification that will be reviewed by recruiter",
    )


class EmailTemplate(BaseModel):
    subject: str = Field(default="", description="Email subject line")
    body: str = Field(
        default="", description="Email body with FULL_NAME as placeholder"
    )


class CvProcessingFinalResult(ParsedCV, PriorityAnalysisResponse):
    email_response_example: EmailTemplate


class CvAnalysisState(TypedDict):
    cv_text: str
    job_description: str
    parsed_cv: ParsedCV
    priority_analysis: PriorityAnalysisResponse
    email_template: EmailTemplate
    final_result: CvProcessingFinalResult
    error: str
