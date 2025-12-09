# JobSpring - AI Core Engine

## Overview
JobSpring is a multi-agent AI engine for the hiring lifecycle. It combines LangGraph orchestration with MCP tools to analyze CVs, score candidates, and automate interview scheduling through Google Workspace (Gmail + Calendar).

## Features
- AI + MCP integration: CV analysis plus calendar management through MCP tools
- Automated scheduling: Cuts manual coordination time by auto-finding meeting slots
- Intelligent screening: Only proceeds with qualified candidates based on AI scoring
- Context-aware communication: Generates personalized interview notes/emails
- Multi-user coordination: Finds times that work for all interviewers
- Production-minded: Creates calendar events with Meet links and structured outputs

## Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) installed
- Google GenAI / Gemini API access (e.g., `GOOGLE_API_KEY`)
- Google Workspace MCP endpoint and credentials for Gmail/Calendar tools (`GOOGLE_WORKSPACE_MCP`)
- Optional model tuning via `LLM_MODEL` and `LLM_TEMPERATURE`

## Setup
1) Install dependencies: `uv pip install -e .`
2) Create a `.env` file (or export env vars) with values such as:
   ```
   GOOGLE_API_KEY=your_google_genai_key
   GOOGLE_WORKSPACE_MCP=https://your-mcp-server
   LLM_MODEL=gemini-2.5-flash
   LLM_TEMPERATURE=1.0
   ```
3) Ensure your Google Workspace MCP server is running and authorized for Gmail/Calendar.

## Running
- FastAPI dev server (reload): `uv run fastapi dev src\main.py` (defaults to http://localhost:8000, OpenAPI at `/api/v1/openapi.json`)
- [MCP server](https://github.com/taylorwilsdon/google_workspace_mcp) : `uv run main.py --transport streamable-http --tools calendar gmail`

## Tests
- Google Workspace integration tests: `uv run python tests\cv_agent\mcp\test_google_workspace.py`
- Calendar tools test: `uv run python tests\cv_agent\mcp\test_g_calendar.py`
- Full suite (if desired): `uv run python -m pytest tests`
