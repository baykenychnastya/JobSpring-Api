I'll help you set up the Google Workspace MCP server locally. Let me first check the repository to understand its structure and requirements.Great! Now I have all the information. Let me create a comprehensive guide for you to set up and run this Google Workspace MCP server locally.

## Complete Setup Guide: Google Workspace MCP Server

### Prerequisites

1. **Python 3.10 or higher**
2. **uv** (Python package installer) - Install with:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Google Cloud Project with OAuth 2.0 credentials**

---

### Step 1: Google Cloud Setup (OAuth Credentials)

#### A. Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

#### B. Create OAuth 2.0 Credentials
1. Navigate to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Choose **Desktop app** as the application type
4. Name it (e.g., "Workspace MCP Server")
5. Click **Create**
6. **Download the JSON file** - you'll need the Client ID and Client Secret

#### C. Enable Required Google APIs
Enable these APIs for your project (click each link while logged into Google Cloud Console):
- [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
- [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
- [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)
- [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com)
- [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
- [Google Slides API](https://console.cloud.google.com/apis/library/slides.googleapis.com)
- [Google Forms API](https://console.cloud.google.com/apis/library/forms.googleapis.com)
- [Google Tasks API](https://console.cloud.google.com/apis/library/tasks.googleapis.com)
- [Google Chat API](https://console.cloud.google.com/apis/library/chat.googleapis.com)

---

### Step 2: Clone and Set Up the Repository

```bash
# Clone the repository
git clone https://github.com/taylorwilsdon/google_workspace_mcp.git
cd google_workspace_mcp

# Install dependencies
uv sync
```

---

### Step 3: Configure OAuth Credentials

You have **three options** for providing credentials:

#### **Option 1: Environment Variables (Recommended for Production)**
```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id-here"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret-here"
export OAUTHLIB_INSECURE_TRANSPORT=1  # For local development only
```

#### **Option 2: .env File (Recommended for Development)**
```bash
# Copy the example env file
cp .env.oauth21 .env

# Edit .env and add your credentials:
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
OAUTHLIB_INSECURE_TRANSPORT=1
```

#### **Option 3: client_secret.json File**
Place the downloaded JSON file from Google Cloud Console in the project root as `client_secret.json`

---

### Step 4: Run the MCP Server

#### **Basic Startup (stdio mode - for Claude Desktop)**
```bash
uv run main.py
```

#### **HTTP Mode (for web-based agents/debugging)**
```bash
uv run main.py --transport streamable-http
```

#### **With Specific Tools Only**
```bash
# Load only Gmail and Drive tools
uv run main.py --tools gmail drive

# Load only Calendar and Tasks
uv run main.py --tools calendar tasks
```

#### **Using Tool Tiers**
```bash
# Core tier (essential tools only)
uv run main.py --tool-tier core

# Extended tier (core + additional features)
uv run main.py --tool-tier extended

# Complete tier (all tools)
uv run main.py --tool-tier complete
```

---

### Step 5: Connect Your Agent to the MCP Server

#### **For Claude Desktop (stdio mode)**

1. Open Claude Desktop settings
2. Navigate to **Developer** → **Edit Config**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add this configuration:

```json
{
  "mcpServers": {
    "google_workspace": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/FULL/PATH/TO/google_workspace_mcp",
        "main.py"
      ],
      "env": {
        "GOOGLE_OAUTH_CLIENT_ID": "your-client-id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "your-client-secret",
        "OAUTHLIB_INSECURE_TRANSPORT": "1"
      }
    }
  }
}
```

Replace `/FULL/PATH/TO/google_workspace_mcp` with the actual path to your cloned repository.

4. Restart Claude Desktop

#### **For HTTP-based Agents (HTTP mode)**

1. Start the server in HTTP mode:
```bash
uv run main.py --transport streamable-http
```

2. The server will be available at: `http://localhost:8000/mcp/`

3. Configure your agent to connect to this URL

For Claude Desktop with HTTP mode:
```json
{
  "mcpServers": {
    "google_workspace": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8000/mcp"]
    }
  }
}
```

---

### Step 6: First-Time Authentication

1. When you first use a tool that requires Google access, the server will:
   - Return an authorization URL
   - Prompt you to open it in your browser
   
2. Open the URL and authorize the application

3. Google will provide an authorization code

4. Paste the code back into the terminal/application

5. The server will complete authentication and cache credentials

---

### Optional: Additional Configuration

#### **Single-User Mode**
```bash
export USER_GOOGLE_EMAIL="your.email@gmail.com"
uv run main.py --single-user
```

#### **Custom Port**
```bash
export WORKSPACE_MCP_PORT=9000
uv run main.py --transport streamable-http
```

#### **Enable OAuth 2.1 (for multi-user support)**
```bash
export MCP_ENABLE_OAUTH21=true
uv run main.py --transport streamable-http
```

#### **Google Custom Search (Optional)**
```bash
export GOOGLE_PSE_API_KEY="your-api-key"
export GOOGLE_PSE_ENGINE_ID="your-engine-id"
```

---

### Testing the Connection

Once configured, test the connection:

1. Open your agent (Claude Desktop, etc.)
2. Try a command like: "List my recent Gmail messages"
3. If authentication is needed, follow the prompts
4. Verify the tool responds with your Gmail data

---

### Troubleshooting

**Issue: "OAuth credentials not found"**
- Ensure you've set `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`
- Verify the credentials are correct from Google Cloud Console

**Issue: "API not enabled"**
- Go back to Google Cloud Console and enable the required APIs

**Issue: "Redirect URI mismatch"**
- For local development, ensure `OAUTHLIB_INSECURE_TRANSPORT=1` is set
- The server uses `http://localhost:8000/oauth2callback` by default

**Issue: Server won't start**
- Check Python version: `python --version` (must be 3.10+)
- Reinstall dependencies: `uv sync`

---

### Available Tools by Service

Once connected, your agent will have access to:
- **Gmail**: Send, read, search emails
- **Drive**: Create, read, update files and folders
- **Calendar**: Manage events, calendars
- **Docs**: Create, edit documents
- **Sheets**: Manage spreadsheets
- **Slides**: Create presentations
- **Forms**: Create and manage forms
- **Tasks**: Manage task lists
- **Chat**: Send messages to Google Chat
- **Search**: Google Custom Search (if configured)

That's it! Your MCP server should now be running and connected to your agent with full Google Workspace access.



RESOLVE 403 - Доступ заблоковано: додаток SpringJob не пройшов процедуру підтвердження від Google
Ah, perfect! Since you're the developer of SpringJob, you need to add your own Google account as a test user in the Google Cloud Console. Here's how to fix this:
Steps to add yourself as a test user:

Go to Google Cloud Console
Select your SpringJob project
Navigate to APIs & Services → OAuth consent screen
Scroll down to the Test users section
Click "+ ADD USERS"
Enter your Google email address (the one you're trying to authenticate with)
Click "Save"

After adding yourself as a test user:

The authorization link should work
You'll be able to grant access to your Google Calendar
The 403 error should be resolved


How to run locally 

Run server with `uv run main.py --transport streamable-http --tools calendar gmail` Important run only with tools enabled in Google cloud console

conect ot it by setting mcp url in GOOGLE_WORKSPACE_MCP
