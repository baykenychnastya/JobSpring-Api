from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    url: HttpUrl = Field(
        alias="GOOGLE_WORKSPACE_MCP", description="Google Workspace MCP server URL"
    )

    llm_model: str = Field(
        default="gemini-2.5-flash", alias="LLM_MODEL", description="LLM model to use"
    )

    llm_temperature: float = Field(
        default=1.0,
        alias="LLM_TEMPERATURE",
        description="LLM temperature setting",
        ge=0.0,
        le=2.0,
    )


google_workspace_mcp_settings = Settings()  # type: ignore
