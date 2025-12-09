"""
LangGraph agent for CV analysis.
"""

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, List, Dict, Any
import json
import logging

from cv_agent.cv_parser import CVParser
from cv_agent.models import (
    CvAnalysisState,
    CvProcessingFinalResult,
    Education,
    EmailTemplate,
    Experience,
    PriorityAnalysisResponse,
    ParsedCV,
)

load_dotenv()

logger = logging.getLogger(__name__)


class CVAnalysisAgent:
    """LangGraph agent for analyzing CVs against job descriptions"""

    def __init__(self):
        """
        Initialize the CV Analysis Agent.
        """
        self.cv_parser = CVParser()

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0,
        )
        self.structured_llm = self.llm.with_structured_output(ParsedCV)
        self.priority_structured_llm = self.llm.with_structured_output(
            PriorityAnalysisResponse
        )
        self.email_structured_llm = self.llm.with_structured_output(EmailTemplate)

        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for CV analysis"""
        workflow = StateGraph(CvAnalysisState)

        workflow.add_node("parse_cv", self._parse_cv)
        workflow.add_node("analyze_priority", self._analyze_priority)
        workflow.add_node("generate_email", self._generate_email)
        workflow.add_node("combine_results", self._combine_results)

        workflow.set_entry_point("parse_cv")
        workflow.add_conditional_edges(
            "parse_cv",
            lambda state: self._decide_next_node(state, "analyze_priority"),
            {"analyze_priority": "analyze_priority", END: END},
        )
        workflow.add_edge("analyze_priority", "generate_email")
        workflow.add_edge("generate_email", "combine_results")
        workflow.add_edge("combine_results", END)

        return workflow

    def _decide_next_node(self, state: CvAnalysisState, nest_node: str):
        if state["error"]:
            return END
        else:
            return nest_node

    async def _parse_cv(self, state: CvAnalysisState) -> CvAnalysisState:
        """Parse CV content into structured format"""
        logger.info("Parsing CV content")

        cv_text = state["cv_text"]

        system_prompt = """You are an expert CV/resume parser. Extract all relevant information from the CV text and structure it accurately.

    Guidelines:
    - Extract all information accurately from the CV
    - Use empty strings for missing text fields
    - Use empty arrays for missing list fields
    - For dates, use the format found in the CV (e.g., "2020", "Jan 2020", "2020-01")
    - For skills, extract both technical and soft skills
    - For summary, create a brief professional summary if not explicitly stated in the CV"""

        user_prompt = f"""Parse the following CV and extract all relevant information:

    CV Text:
    {cv_text}"""

        try:
            parsed_cv: ParsedCV = await self.structured_llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )  # type: ignore

            state["parsed_cv"] = parsed_cv
            logger.info("CV parsed successfully")

        except Exception as e:
            logger.error(f"Error parsing CV: {e}")
            state["error"] = f"Error parsing CV: {str(e)}"
            state["parsed_cv"] = self._get_empty_cv_structure()

        return state

    async def _analyze_priority(self, state: CvAnalysisState) -> CvAnalysisState:
        """Analyze candidate priority based on CV and job description"""
        logger.info("Analyzing candidate priority")

        parsed_cv = state["parsed_cv"]
        job_description = state["job_description"]

        system_prompt = """You are an expert recruiter and talent acquisition specialist. 
        Analyze the candidate's CV against the job description and determine their fit level.

    Priority levels:
    - "highly-recommended": Exceptional match, meets or exceeds all key requirements
    - "recommended": Good match, meets most requirements with minor gaps
    - "not-recommended": Significant gaps in key requirements

    Provide a 2-4 sentence explanation that will be sent directly to the candidate as feedback."""

        user_prompt = f"""Analyze this candidate against the job description:

    JOB DESCRIPTION:
    {job_description}

    CANDIDATE CV:
    Name: {parsed_cv.full_name or "Unknown"}
    Summary: {parsed_cv.summary or "N/A"}
    Skills: {", ".join(parsed_cv.skills or [])}
    Languages: {", ".join(parsed_cv.languages or [])}

    Experience:
    {self._format_experience(parsed_cv.experience or [])}

    Education:
    {self._format_education(parsed_cv.education or [])}

    Certifications: {", ".join(parsed_cv.certifications or [])}

    Determine the priority level and provide clear, constructive feedback."""

        try:
            priority_analysis: PriorityAnalysisResponse = (
                await self.priority_structured_llm.ainvoke(
                    [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt),
                    ]
                )
            )  # type: ignore

            state["priority_analysis"] = priority_analysis
            logger.info(f"Priority analysis completed: {priority_analysis.priority}")

        except Exception as e:
            logger.error(f"Error analyzing priority: {e}")
            state["priority_analysis"] = PriorityAnalysisResponse(
                priority="not-recommended",
                priority_description="Unable to complete analysis due to technical error.",
            )
            state["error"] = f"Error analyzing priority: {e}"

        return state

    async def _generate_email(self, state: CvAnalysisState) -> CvAnalysisState:
        """Generate email template based on priority analysis"""
        logger.info("Generating email template")

        priority_analysis = state["priority_analysis"]
        job_description = state["job_description"]
        priority = priority_analysis.priority

        system_prompt = """You are a professional recruiter crafting personalized email responses to job applicants. 
    Generate a professional, empathetic email template based on the candidate's priority level.

    CRITICAL: 
    - Use "FULL_NAME" as a placeholder for the candidate's name (NOT their actual name)
    - Use "AVAILABLE_SLOTS" as a placeholder for interview time slots (the recruiter will replace this later)

    Email guidelines:
    - Be professional, respectful, and empathetic
    - Use "FULL_NAME" placeholder (the recruiter will replace this later)
    - Use "AVAILABLE_SLOTS" placeholder when mentioning interview scheduling
    - For highly-recommended: Express enthusiasm and outline next steps
    - For recommended: Be positive but mention areas for consideration
    - For not-recommended: Be respectful and encouraging, suggest staying connected
    - Keep the tone warm but professional
    - Include clear next steps or closing statement"""

        if priority == "highly-recommended":
            user_prompt = f"""Create an email for a HIGHLY RECOMMENDED candidate.

    Job Description (for context):
    {job_description}

    Feedback: {priority_analysis.priority_description}

    The email should:
    - Express genuine excitement about their qualifications
    - Mention specific strengths from the feedback
    - Outline next steps in the interview process
    - Use "FULL_NAME" as placeholder for their name
    - Use "AVAILABLE_SLOTS" as placeholder when proposing interview times"""

        elif priority == "recommended":
            user_prompt = f"""Create an email for a RECOMMENDED candidate.

    Job Description (for context):
    {job_description}

    Feedback: {priority_analysis.priority_description}

    The email should:
    - Show appreciation for their application
    - Acknowledge their qualifications
    - Mention next steps or timeline
    - Use "FULL_NAME" as placeholder for their name
    - Use "AVAILABLE_SLOTS" as placeholder when proposing interview times"""

        else:
            user_prompt = f"""Create an email for a NOT RECOMMENDED candidate.

    Job Description (for context):
    {job_description}

    Feedback: {priority_analysis.priority_description}

    The email should:
    - Thank them for their interest and time
    - Be respectful and empathetic
    - Provide constructive feedback if appropriate
    - Encourage them to apply for future positions
    - Wish them well in their job search
    - Use "FULL_NAME" as placeholder for their name"""

        try:
            email_template: EmailTemplate = await self.email_structured_llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )  # type: ignore

            state["email_template"] = email_template
            logger.info("Email template generated successfully")

        except Exception as e:
            logger.error(f"Error generating email: {e}")
            state["email_template"] = EmailTemplate(
                subject="Thank you for your application",
                body="Dear FULL_NAME,\n\nThank you for your interest in our position.\n\nBest regards",
            )

        return state

    def _combine_results(self, state: CvAnalysisState) -> CvAnalysisState:
        """Combine parsed CV and priority analysis into final result"""
        logger.info("Combining results")

        parsed_cv = state["parsed_cv"]
        priority_analysis = state["priority_analysis"]
        email_template = state.get("email_template", EmailTemplate(subject="", body=""))

        final_result = CvProcessingFinalResult(
            **parsed_cv.model_dump(),
            **priority_analysis.model_dump(),
            email_response_example=email_template,
        )

        state["final_result"] = final_result
        return state

    def _format_experience(self, experience_list: List[Experience]) -> str:
        """Format experience list for prompt"""
        if not experience_list:
            return "No experience listed"

        formatted = []
        for exp in experience_list:
            formatted.append(
                f"- {exp.job_title or 'N/A'} at {exp.company or 'N/A'} "
                f"({exp.start_date or 'N/A'} - {exp.end_date or 'N/A'})"
            )
        return "\n".join(formatted)

    def _format_education(self, education_list: List[Education]) -> str:
        """Format education list for prompt"""
        if not education_list:
            return "No education listed"

        formatted = []
        for edu in education_list:
            formatted.append(
                f"- {edu.degree or 'N/A'} in {edu.field or 'N/A'} "
                f"from {edu.institution or 'N/A'} "
                f"({edu.start_year or 'N/A'} - {edu.end_year or 'N/A'})"
            )
        return "\n".join(formatted)

    def _get_empty_cv_structure(self) -> ParsedCV:
        """Return empty CV structure"""
        return ParsedCV()

    async def analyze_cv(
        self, cv_file_path: str, job_description: str
    ) -> CvProcessingFinalResult:
        """
        Analyze a CV against a job description.

        Args:
            cv_file_path: Path to the CV file
            job_description: Job description text

        Returns:
            Dictionary containing the structured CV analysis
        """
        logger.info(f"Starting CV analysis for file: {cv_file_path}")

        cv_text = self.cv_parser.extract_text(cv_file_path)

        if not cv_text or len(cv_text.strip()) < 50:
            raise ValueError("CV file is empty or could not be read properly")

        initial_state: CvAnalysisState = {
            "cv_text": cv_text,
            "job_description": job_description,
            "parsed_cv": ParsedCV(),
            "priority_analysis": PriorityAnalysisResponse(),
            "email_template": EmailTemplate(),
            "final_result": CvProcessingFinalResult(
                email_response_example=EmailTemplate()
            ),
            "error": "",
        }

        final_state = await self.app.ainvoke(initial_state)

        if final_state.get("error"):
            logger.error(f"Error in workflow: {final_state['error']}")

        return final_state["final_result"]
