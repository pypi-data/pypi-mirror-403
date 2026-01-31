# WARNING

⚠️ THIS HAS MOSTLY BEEN CODED VIA AI - PROCEED AT YOUR OWN RISK⚠️ 

# Clockify MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with the Clockify time tracking API. This server enables AI assistants to interact with Clockify for time tracking, reporting, and team management tasks.

## Features

### Core Functionality
- 🔍 **Find time entries** by user, project, or search phrase
- ⏱️ **Start and stop timers** with project association
- ➕ **Add time entries** for any user with flexible parameters
- 📊 **High-level analysis** tools for team management
- 📈 **Weekly summaries** and overtime detection

### High-Level Tools
- **Find overtime users**: Identify team members working >40 hours/week
- **Find undertime users**: Identify team members logging <20 hours/week
- **Weekly summaries**: Get detailed breakdowns of hours by week
- **Project analytics**: See who's working on what and for how long

## Installation

### Prerequisites
- Python 3.10 or higher
- Clockify API key ([Get one here](https://clockify.me/user/settings))

### Quick Install with uvx

The easiest way to use this server is with `uvx` (bundled with `uv`):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the server directly (it will be cached)
uvx clockify-mcp-server
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/clockify-mcp-server.git
cd clockify-mcp-server

# Install with pip
pip install -e .

# Or install from PyPI (once published)
pip install clockify-mcp-server
```

## Configuration

### Environment Variables

Set your Clockify API key as an environment variable:

```bash
export CLOCKIFY_API_KEY="your_api_key_here"
```

You can get your API key from [Clockify User Settings](https://clockify.me/user/settings) under "API" section.

### MCP Client Configuration

Add this to your MCP client configuration file:

#### For Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "clockify": {
      "command": "uvx",
      "args": ["clockify-mcp-server"],
      "env": {
        "CLOCKIFY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### For Opencode

```json
{
  "mcp": {
    "clockify": {
      "command": ["uvx", "clockify-mcp-server"]
      "environment": {
        "CLOCKIFY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

### 1. `find_user_time_entries`
Find all time entries for a specific user.

**Parameters:**
- `user_name` (required): Name of the user (partial match, case-insensitive)
- `start_date` (optional): Start date in YYYY-MM-DD format (default: 30 days ago)
- `end_date` (optional): End date in YYYY-MM-DD format (default: today)
- `limit` (optional): Maximum entries to display (default: 50, use 0 for unlimited)
- `workspace_id` (optional): Workspace ID (default: user's default workspace)

**Example:**
```
Find all time entries for John Doe from the last 30 days
```

### 2. `find_project_time_entries`
Find all time entries for a specific project.

**Parameters:**
- `project_name` (required): Name of the project (partial match, case-insensitive)
- `start_date` (optional): Start date in YYYY-MM-DD format (default: 30 days ago)
- `end_date` (optional): End date in YYYY-MM-DD format (default: today)
- `limit` (optional): Maximum entries to display (default: 30, use 0 for unlimited)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Show me all time logged to the "Website Redesign" project this month
```

### 3. `search_time_entries`
Search time entries by description phrase.

**Parameters:**
- `search_phrase` (required): Phrase to search for in descriptions
- `user_name` (optional): Limit search to specific user
- `start_date` (optional): Start date in YYYY-MM-DD format (default: 30 days ago)
- `end_date` (optional): End date in YYYY-MM-DD format (default: today)
- `limit` (optional): Maximum entries to display (default: 50, use 0 for unlimited)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Find all time entries containing "meeting" in the description
```

### 4. `add_time_entry`
Add a time entry for a specific user.

**Parameters:**
- `user_name` (required): Name of the user
- `description` (required): Description of the work
- `start_time` (required): Start time in ISO format (e.g., 2024-01-29T09:00:00)
- `end_time` (required): End time in ISO format (e.g., 2024-01-29T17:00:00)
- `project_name` (optional): Project to associate with
- `task_name` (optional): Task within the project (requires project_name)
- `billable` (optional): Whether time is billable (default: true)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Add a time entry for Jane Smith: 8 hours today on "Client Project" for meetings
```

### 5. `start_timer`
Start a timer for the current user.

**Parameters:**
- `description` (required): What you're working on
- `project_name` (optional): Project to associate with
- `task_name` (optional): Task within the project (requires project_name)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Start a timer for "Writing documentation" on the "Internal Tools" project
```

### 6. `stop_timer`
Stop the currently running timer.

**Parameters:**
- `workspace_id` (optional): Workspace ID

**Example:**
```
Stop my current timer
```

### 7. `find_overtime_users`
Find users working more than specified hours per week.

**Parameters:**
- `hours_threshold` (optional): Hours per week threshold (default: 40)
- `weeks` (optional): Number of weeks to analyze (default: 4)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Show me team members who worked more than 40 hours in any week this month
```

### 8. `find_undertime_users`
Find users who didn't log minimum hours per week.

**Parameters:**
- `hours_threshold` (optional): Minimum hours threshold (default: 20)
- `weeks` (optional): Number of weeks to analyze (default: 1)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Who didn't log at least 20 hours last week?
```

### 9. `get_user_weekly_summary`
Get a weekly breakdown of hours for a user.

**Parameters:**
- `user_name` (required): Name of the user
- `weeks` (optional): Number of weeks to analyze (default: 4)
- `workspace_id` (optional): Workspace ID

**Example:**
```
Show me John's weekly hours for the past month
```

## Usage Examples

### With Claude Desktop

Once configured, you can ask Claude natural language questions:

```
"Find all time entries for Sarah Johnson from last week"

"Show me everyone who logged time to the Mobile App project this month"

"Start a timer for code review on the Backend API project"

"Who on the team worked more than 45 hours in the past month?"

"Add a time entry for Mike: 4 hours yesterday on Client Presentation"
```

### Programmatic Usage

```python
from clockify_mcp import ClockifyClient
import asyncio

async def main():
    client = ClockifyClient(api_key="your_api_key")
    
    # Get current user
    user = await client.get_current_user()
    print(f"Logged in as: {user['name']}")
    
    # Get default workspace
    workspace = await client.get_default_workspace()
    
    # Find a user
    user = await client.find_user_by_name(workspace['id'], "John")
    
    # Get their time entries
    entries = await client.get_time_entries(
        workspace_id=workspace['id'],
        user_id=user['id']
    )
    
    print(f"Found {len(entries)} time entries")
    
    await client.close()

asyncio.run(main())
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/KeithHanson/clockify-mcp
cd clockify-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Project Structure

```
clockify-mcp-server/
├── src/
│   └── clockify_mcp/
│       ├── __init__.py
│       ├── client.py      # Clockify API client
│       └── server.py      # MCP server implementation
├── docs/                   # Full API documentation
│   ├── 00_INDEX.md
│   ├── 01_USER_API.md
│   ├── 02_WORKSPACE_API.md
│   ├── 03_TIME_ENTRY_API.md
│   ├── 04_PROJECT_API.md
│   ├── 05_REPORTS_API.md
│   ├── 06_WEBHOOKS_API.md
│   └── 07_QUICK_REFERENCE.md
├── tests/                  # Test suite
├── pyproject.toml         # Project configuration
├── README.md              # This file
└── LICENSE                # MIT License
```

## API Documentation

Complete API documentation is available in the `docs/` directory:

- **00_INDEX.md** - Overview and quick reference
- **01_USER_API.md** - User management endpoints
- **02_WORKSPACE_API.md** - Workspace configuration
- **03_TIME_ENTRY_API.md** - Time tracking operations
- **04_PROJECT_API.md** - Project management
- **05_REPORTS_API.md** - Reporting and analytics
- **06_WEBHOOKS_API.md** - Webhook configuration (not implemented in MCP server)
- **07_QUICK_REFERENCE.md** - Code snippets and examples

## Limitations

- **User-specific operations**: Some operations (like adding time entries for other users) may require workspace admin permissions
- **Rate limiting**: The server respects Clockify's rate limits (50 requests/second for addon tokens)
- **Workspace selection**: Defaults to user's default workspace if not specified
- **Webhooks**: Not implemented (not needed for MCP use case)

## Troubleshooting

### "CLOCKIFY_API_KEY environment variable is required"

Make sure you've set the API key in your environment or MCP configuration:

```bash
export CLOCKIFY_API_KEY="your_key_here"
```

### "User not found"

User names are matched using partial, case-insensitive search. Try:
- Using just the first or last name
- Checking spelling
- Using the email address instead

### "No workspaces found"

Ensure your API key is valid and you have access to at least one workspace in Clockify.

### Connection Issues

If you're having connection issues:
1. Check your internet connection
2. Verify your API key is correct
3. Ensure you're not behind a proxy that blocks API requests

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io/)
- Integrates with [Clockify](https://clockify.me/) time tracking
- Documentation derived from official Clockify API docs

## Support

- **Issues**: [GitHub Issues](https://github.com/KeithHanson/clockify-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/KeithHanson/clockify-mcp/discussions)
- **Clockify API**: [docs.clockify.me](https://docs.clockify.me/)

## Changelog

### v0.1.0 (Initial Release)
- Core time entry operations
- User and project search
- Timer start/stop functionality
- High-level analysis tools
- Overtime/undertime detection
- Weekly summaries
