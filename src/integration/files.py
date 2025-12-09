import logging
from fastapi import HTTPException
import httpx

logger = logging.getLogger(__name__)


async def download(file_url: str) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            file_response = await client.get(file_url)
            file_response.raise_for_status()
            return file_response
        except httpx.HTTPError as e:
            logger.error(f"Failed to download file from URL: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download file from URL: {str(e)}",
            )
