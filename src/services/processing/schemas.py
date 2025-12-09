from pydantic import BaseModel, Field
from typing import List, Literal


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


class CVAnalysisRequest(BaseModel):
    fileUrl: str
    jobDescription: str


class EmailResponse(BaseModel):
    subject: str
    body: str


class CVAnalysisResponse(BaseModel):
    full_name: str = ""
    contact: Contact = Field(default_factory=Contact)
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    priority: Literal["recommended", "highly-recommended", "not-recommended"]
    priority_description: str
    email_response_example: EmailResponse
