import logging
from pathlib import Path
import tempfile
from fastapi import APIRouter, HTTPException

from cv_agent.agent import CVAnalysisAgent
from cv_agent.models import CvProcessingFinalResult
from services.processing.schemas import CVAnalysisRequest, CVAnalysisResponse
from integration import files

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing")

agent = CVAnalysisAgent()


@router.post("/analyze-cv", response_model=CVAnalysisResponse)
async def analyze_cv(request: CVAnalysisRequest) -> CVAnalysisResponse:
    """
    Analyze a CV against a job description using LangGraph agent.

    Returns:
        CVAnalysisResponse: Structured analysis of the CV
    """
    try:
        logger.info(f"Received CV analysis request for file: {request.fileUrl}")

        file_response = await files.download(request.fileUrl)

        # Determine file extension from URL or Content-Type
        file_url_path = Path(request.fileUrl)
        file_extension = file_url_path.suffix.lower()

        # If no extension in URL, try to get it from Content-Type header
        if not file_extension:
            content_type = file_response.headers.get("content-type", "").lower()
            extension_map = {
                "application/pdf": ".pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                "application/msword": ".doc",
                "text/plain": ".txt",
            }
            file_extension = extension_map.get(content_type, ".pdf")

        # Validate file type
        allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}",
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            temp_file.write(file_response.content)
            temp_file_path = temp_file.name

        try:
            # Run the LangGraph agent
            logger.info("Starting CV analysis with LangGraph agent")
            result: CvProcessingFinalResult = await agent.analyze_cv(
                temp_file_path, request.jobDescription
            )

            logger.info(
                f"CV analysis completed successfully for {result.full_name or 'Unknown'}"
            )
            return CVAnalysisResponse.model_validate(result.model_dump())
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing CV: {str(e)}")
