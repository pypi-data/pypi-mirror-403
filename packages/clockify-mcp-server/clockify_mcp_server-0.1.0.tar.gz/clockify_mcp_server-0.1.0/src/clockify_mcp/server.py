"""
Clockify MCP Server
Provides MCP tools for interacting with Clockify time tracking
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

from .client import ClockifyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("clockify-mcp-server")

# Global client instance
client: Optional[ClockifyClient] = None


def get_client() -> ClockifyClient:
    """Get or create Clockify client"""
    global client
    if client is None:
        api_key = os.getenv("CLOCKIFY_API_KEY")
        if not api_key:
            raise ValueError("CLOCKIFY_API_KEY environment variable is required")
        client = ClockifyClient(api_key)
    return client


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="find_user_time_entries",
            description=(
                "Find all time entries for a specific user by their name. "
                "Searches across a date range (defaults to last 30 days) and returns "
                "all time entries with descriptions, projects, and durations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_name": {
                        "type": "string",
                        "description": "Name of the user (partial match, case-insensitive)",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (optional, defaults to today)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of entries to display (optional, defaults to 50, use 0 for unlimited)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": ["user_name"],
            },
        ),
        Tool(
            name="find_project_time_entries",
            description=(
                "Find all time entries for a specific project. "
                "Returns time entries from all users who have logged time to the project."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (partial match, case-insensitive)",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (optional, defaults to today)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of entries to display (optional, defaults to 30, use 0 for unlimited)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="search_time_entries",
            description=(
                "Search time entries by description phrase. "
                "Searches across all users and returns entries containing the search phrase."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search_phrase": {
                        "type": "string",
                        "description": "Phrase to search for in time entry descriptions",
                    },
                    "user_name": {
                        "type": "string",
                        "description": "Optional: limit search to specific user",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (optional, defaults to today)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of entries to display (optional, defaults to 50, use 0 for unlimited)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": ["search_phrase"],
            },
        ),
        Tool(
            name="add_time_entry",
            description=(
                "Add a time entry for a specific user. "
                "Creates a completed time entry with start and end times."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_name": {
                        "type": "string",
                        "description": "Name of the user to add time for",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the work performed",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (e.g., 2024-01-29T09:00:00)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format (e.g., 2024-01-29T17:00:00)",
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Optional: project name to associate with the entry",
                    },
                    "task_name": {
                        "type": "string",
                        "description": "Optional: task name within the project (requires project_name)",
                    },
                    "billable": {
                        "type": "boolean",
                        "description": "Whether the time is billable (default: true)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": ["user_name", "description", "start_time", "end_time"],
            },
        ),
        Tool(
            name="start_timer",
            description=(
                "Start a timer for the current user. "
                "Creates a running time entry without an end time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of what you're working on",
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Optional: project name to associate with the timer",
                    },
                    "task_name": {
                        "type": "string",
                        "description": "Optional: task name within the project (requires project_name)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="stop_timer",
            description=("Stop the currently running timer for the current user."),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="find_overtime_users",
            description=(
                "Find users who have logged more than a specified number of hours per week "
                "in the past month. Useful for identifying overworked team members."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hours_threshold": {
                        "type": "number",
                        "description": "Hours threshold per week (default: 40)",
                    },
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to analyze (default: 4)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="find_undertime_users",
            description=(
                "Find users who have not logged at least a specified number of hours "
                "per week. Useful for identifying team members who may need support."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hours_threshold": {
                        "type": "number",
                        "description": "Minimum hours threshold per week (default: 20)",
                    },
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to analyze (default: 1)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_user_weekly_summary",
            description=(
                "Get a summary of hours logged by a user for each week in the past month."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_name": {"type": "string", "description": "Name of the user"},
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to analyze (default: 4)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID (optional, uses default workspace if not provided)",
                    },
                },
                "required": ["user_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    try:
        client = get_client()

        # Get workspace
        workspace_id = arguments.get("workspace_id")
        if not workspace_id:
            workspace = await client.get_default_workspace()
            workspace_id = workspace["id"]

        # Parse dates if provided
        def parse_date(date_str: Optional[str], default: datetime) -> datetime:
            if date_str:
                return datetime.strptime(date_str, "%Y-%m-%d")
            return default

        # ====================================================================
        # Tool: find_user_time_entries
        # ====================================================================
        if name == "find_user_time_entries":
            user_name = arguments["user_name"]
            start_date = parse_date(
                arguments.get("start_date"), datetime.utcnow() - timedelta(days=30)
            )
            end_date = parse_date(arguments.get("end_date"), datetime.utcnow())
            limit = arguments.get("limit", 50)  # Default to 50, 0 means unlimited

            # Find user
            user = await client.find_user_by_name(workspace_id, user_name)
            if not user:
                return [
                    TextContent(
                        type="text", text=f"User '{user_name}' not found in workspace"
                    )
                ]

            # Get time entries
            entries = await client.get_time_entries(
                workspace_id=workspace_id,
                user_id=user["id"],
                start=start_date,
                end=end_date,
            )

            # Format response
            total_hours = sum(
                client.parse_duration_to_hours(
                    e.get("timeInterval", {}).get("duration", "PT0S")
                )
                for e in entries
            )

            result = f"Found {len(entries)} time entries for {user['name']} ({user['email']})\n"
            result += f"Total hours: {total_hours:.2f}\n"
            result += f"Period: {start_date.date()} to {end_date.date()}\n\n"

            # Apply limit (0 means unlimited)
            display_entries = entries if limit == 0 else entries[:limit]

            if limit > 0 and len(entries) > limit:
                result += f"Showing {limit} of {len(entries)} entries:\n"

            for entry in display_entries:
                interval = entry.get("timeInterval", {})
                duration = client.parse_duration_to_hours(
                    interval.get("duration", "PT0S")
                )
                desc = entry.get("description", "No description")
                project = entry.get("project", {}).get("name", "No project")
                start = interval.get("start", "")[:10]  # Just the date

                result += f"• {start} | {duration:.2f}h | {project} | {desc}\n"

            if limit > 0 and len(entries) > limit:
                result += f"\n... and {len(entries) - limit} more entries (use limit=0 to show all)"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: find_project_time_entries
        # ====================================================================
        elif name == "find_project_time_entries":
            project_name = arguments["project_name"]
            start_date = parse_date(
                arguments.get("start_date"), datetime.utcnow() - timedelta(days=30)
            )
            end_date = parse_date(arguments.get("end_date"), datetime.utcnow())
            limit = arguments.get("limit", 30)  # Default to 30, 0 means unlimited

            # Find project
            project = await client.find_project_by_name(workspace_id, project_name)
            if not project:
                return [
                    TextContent(
                        type="text",
                        text=f"Project '{project_name}' not found in workspace",
                    )
                ]

            # Get time entries for project using the standard API
            # (avoids the Reports API which requires a paid plan)
            entries = await client.get_project_time_entries(
                workspace_id=workspace_id,
                project_id=project["id"],
                start=start_date,
                end=end_date,
            )

            # Calculate total hours
            total_hours = sum(
                client.parse_duration_to_hours(
                    e.get("timeInterval", {}).get("duration", "PT0S")
                )
                for e in entries
            )

            result = (
                f"Found {len(entries)} time entries for project '{project['name']}'\n"
            )
            result += f"Total hours: {total_hours:.2f}\n"
            result += f"Period: {start_date.date()} to {end_date.date()}\n\n"

            # Group by user
            user_hours = {}
            for entry in entries:
                user_name = entry.get("_user", {}).get("name", "Unknown")
                duration = entry.get("timeInterval", {}).get("duration", "PT0S")
                hours = client.parse_duration_to_hours(duration)
                user_hours[user_name] = user_hours.get(user_name, 0.0) + hours

            result += "Hours by user:\n"
            for user_name, hours in sorted(
                user_hours.items(), key=lambda x: x[1], reverse=True
            ):
                result += f"  {user_name}: {hours:.2f}h\n"

            # Apply limit (0 means unlimited)
            display_entries = entries if limit == 0 else entries[:limit]

            if limit > 0 and len(entries) > limit:
                result += f"\nRecent entries (showing {limit} of {len(entries)}):\n"
            else:
                result += f"\nRecent entries:\n"

            for entry in display_entries:
                user_name = entry.get("_user", {}).get("name", "Unknown")
                desc = entry.get("description", "No description")
                duration = client.parse_duration_to_hours(
                    entry.get("timeInterval", {}).get("duration", "PT0S")
                )
                start = entry.get("timeInterval", {}).get("start", "")[:10]

                result += f"• {start} | {user_name} | {duration:.2f}h | {desc}\n"

            if limit > 0 and len(entries) > limit:
                result += f"\n... and {len(entries) - limit} more entries (use limit=0 to show all)"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: search_time_entries
        # ====================================================================
        elif name == "search_time_entries":
            search_phrase = arguments["search_phrase"]
            user_name = arguments.get("user_name")
            start_date = parse_date(
                arguments.get("start_date"), datetime.utcnow() - timedelta(days=30)
            )
            end_date = parse_date(arguments.get("end_date"), datetime.utcnow())
            limit = arguments.get("limit", 50)  # Default to 50, 0 means unlimited

            # Find user if specified
            user_id = None
            if user_name:
                user = await client.find_user_by_name(workspace_id, user_name)
                if not user:
                    return [
                        TextContent(
                            type="text",
                            text=f"User '{user_name}' not found in workspace",
                        )
                    ]
                user_id = user["id"]

            # If no user specified, search all users
            if user_id:
                entries = await client.search_time_entries(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    search_phrase=search_phrase,
                    start=start_date,
                    end=end_date,
                )
            else:
                # Get all users and search their entries
                users = await client.get_workspace_users(workspace_id)
                entries = []
                for user in users:
                    user_entries = await client.search_time_entries(
                        workspace_id=workspace_id,
                        user_id=user["id"],
                        search_phrase=search_phrase,
                        start=start_date,
                        end=end_date,
                    )
                    # Add user info to entries
                    for entry in user_entries:
                        entry["_user"] = user
                    entries.extend(user_entries)

            total_hours = sum(
                client.parse_duration_to_hours(
                    e.get("timeInterval", {}).get("duration", "PT0S")
                )
                for e in entries
            )

            result = f"Found {len(entries)} time entries matching '{search_phrase}'\n"
            result += f"Total hours: {total_hours:.2f}\n"
            result += f"Period: {start_date.date()} to {end_date.date()}\n\n"

            # Apply limit (0 means unlimited)
            display_entries = entries if limit == 0 else entries[:limit]

            if limit > 0 and len(entries) > limit:
                result += f"Showing {limit} of {len(entries)} entries:\n"

            for entry in display_entries:
                interval = entry.get("timeInterval", {})
                duration = client.parse_duration_to_hours(
                    interval.get("duration", "PT0S")
                )
                desc = entry.get("description", "No description")
                project = entry.get("project", {}).get("name", "No project")
                start = interval.get("start", "")[:10]

                # Get user name
                if "_user" in entry:
                    user_display = entry["_user"]["name"]
                else:
                    user_display = "Current user"

                result += f"• {start} | {user_display} | {duration:.2f}h | {project} | {desc}\n"

            if limit > 0 and len(entries) > limit:
                result += f"\n... and {len(entries) - limit} more entries (use limit=0 to show all)"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: add_time_entry
        # ====================================================================
        elif name == "add_time_entry":
            user_name = arguments["user_name"]
            description = arguments["description"]
            start_time = datetime.fromisoformat(arguments["start_time"])
            end_time = datetime.fromisoformat(arguments["end_time"])
            project_name = arguments.get("project_name")
            task_name = arguments.get("task_name")
            billable = arguments.get("billable", True)

            # Find user
            user = await client.find_user_by_name(workspace_id, user_name)
            if not user:
                return [
                    TextContent(
                        type="text", text=f"User '{user_name}' not found in workspace"
                    )
                ]

            # Find project if specified
            project_id = None
            project = None
            if project_name:
                project = await client.find_project_by_name(workspace_id, project_name)
                if not project:
                    return [
                        TextContent(
                            type="text",
                            text=f"Project '{project_name}' not found in workspace",
                        )
                    ]
                project_id = project["id"]

            # Find task if specified (requires project)
            task_id = None
            task = None
            if task_name:
                if not project_id:
                    return [
                        TextContent(
                            type="text",
                            text="Task requires a project. Please specify project_name.",
                        )
                    ]
                task = await client.find_task_by_name(
                    workspace_id, project_id, task_name
                )
                if not task:
                    # List available tasks to help the user
                    available_tasks = await client.get_project_tasks(
                        workspace_id, project_id
                    )
                    task_list = ", ".join([t["name"] for t in available_tasks[:10]])
                    return [
                        TextContent(
                            type="text",
                            text=f"Task '{task_name}' not found in project '{project_name}'.\nAvailable tasks: {task_list}",
                        )
                    ]
                task_id = task["id"]

            # Create time entry
            entry = await client.create_time_entry(
                workspace_id=workspace_id,
                start=start_time,
                end=end_time,
                description=description,
                project_id=project_id,
                task_id=task_id,
                billable=billable,
            )

            duration = client.parse_duration_to_hours(
                entry.get("timeInterval", {}).get("duration", "PT0S")
            )

            result = f"Time entry created successfully\n"
            result += f"User: {user['name']}\n"
            result += f"Duration: {duration:.2f} hours\n"
            result += f"Description: {description}\n"
            result += f"Start: {start_time}\n"
            result += f"End: {end_time}\n"
            if project:
                result += f"Project: {project['name']}\n"
            if task:
                result += f"Task: {task['name']}\n"
            result += f"Billable: {billable}\n"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: start_timer
        # ====================================================================
        elif name == "start_timer":
            description = arguments["description"]
            project_name = arguments.get("project_name")
            task_name = arguments.get("task_name")

            # Find project if specified
            project_id = None
            project = None
            if project_name:
                project = await client.find_project_by_name(workspace_id, project_name)
                if not project:
                    return [
                        TextContent(
                            type="text",
                            text=f"Project '{project_name}' not found in workspace",
                        )
                    ]
                project_id = project["id"]

            # Find task if specified (requires project)
            task_id = None
            task = None
            if task_name:
                if not project_id:
                    return [
                        TextContent(
                            type="text",
                            text="Task requires a project. Please specify project_name.",
                        )
                    ]
                task = await client.find_task_by_name(
                    workspace_id, project_id, task_name
                )
                if not task:
                    available_tasks = await client.get_project_tasks(
                        workspace_id, project_id
                    )
                    task_list = ", ".join([t["name"] for t in available_tasks[:10]])
                    return [
                        TextContent(
                            type="text",
                            text=f"Task '{task_name}' not found in project '{project_name}'.\nAvailable tasks: {task_list}",
                        )
                    ]
                task_id = task["id"]

            # Start timer
            entry = await client.start_timer(
                workspace_id=workspace_id,
                description=description,
                project_id=project_id,
                task_id=task_id,
            )

            result = f"Timer started successfully\n"
            result += f"Description: {description}\n"
            if project:
                result += f"Project: {project['name']}\n"
            if task:
                result += f"Task: {task['name']}\n"
            result += f"Started at: {entry.get('timeInterval', {}).get('start', '')}\n"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: stop_timer
        # ====================================================================
        elif name == "stop_timer":
            # Get current user
            user = await client.get_current_user()

            # Check for running timer
            running = await client.get_running_timer(workspace_id, user["id"])
            if not running:
                return [TextContent(type="text", text="No running timer found")]

            # Stop timer
            entry = await client.stop_timer(workspace_id, user["id"])

            duration = client.parse_duration_to_hours(
                entry.get("timeInterval", {}).get("duration", "PT0S")
            )

            result = f"✓ Timer stopped successfully\n"
            result += f"Duration: {duration:.2f} hours\n"
            result += f"Description: {entry.get('description', 'No description')}\n"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: find_overtime_users
        # ====================================================================
        elif name == "find_overtime_users":
            hours_threshold = arguments.get("hours_threshold", 40)
            weeks = arguments.get("weeks", 4)

            # Get all active users
            users = await client.get_workspace_users(workspace_id)

            # Calculate start date
            start_date = datetime.utcnow() - timedelta(weeks=weeks)

            overtime_users = []

            for user in users:
                weekly_hours = await client.calculate_weekly_hours(
                    workspace_id=workspace_id, user_id=user["id"], start_date=start_date
                )

                # Check if any week exceeds threshold
                for week, hours in weekly_hours.items():
                    if hours > hours_threshold:
                        overtime_users.append(
                            {"user": user, "week": week, "hours": hours}
                        )

            if not overtime_users:
                return [
                    TextContent(
                        type="text",
                        text=f"No users found working more than {hours_threshold} hours/week",
                    )
                ]

            result = f"Users working more than {hours_threshold} hours/week:\n\n"

            # Group by user
            user_overtime = {}
            for ot in overtime_users:
                user_name = ot["user"]["name"]
                if user_name not in user_overtime:
                    user_overtime[user_name] = []
                user_overtime[user_name].append((ot["week"], ot["hours"]))

            for user_name, weeks_data in user_overtime.items():
                result += f"**{user_name}**\n"
                for week, hours in sorted(weeks_data):
                    result += f"  Week of {week}: {hours:.2f} hours\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: find_undertime_users
        # ====================================================================
        elif name == "find_undertime_users":
            hours_threshold = arguments.get("hours_threshold", 20)
            weeks = arguments.get("weeks", 1)

            # Get all active users
            users = await client.get_workspace_users(workspace_id)

            # Calculate start date
            start_date = datetime.utcnow() - timedelta(weeks=weeks)

            undertime_users = []

            for user in users:
                weekly_hours = await client.calculate_weekly_hours(
                    workspace_id=workspace_id, user_id=user["id"], start_date=start_date
                )

                # Check if any week is below threshold
                for week, hours in weekly_hours.items():
                    if hours < hours_threshold:
                        undertime_users.append(
                            {"user": user, "week": week, "hours": hours}
                        )

            if not undertime_users:
                return [
                    TextContent(
                        type="text",
                        text=f"All users logged at least {hours_threshold} hours/week in the past {weeks} week(s)",
                    )
                ]

            result = f"Users who logged less than {hours_threshold} hours/week:\n\n"

            # Group by user
            user_undertime = {}
            for ut in undertime_users:
                user_name = ut["user"]["name"]
                if user_name not in user_undertime:
                    user_undertime[user_name] = []
                user_undertime[user_name].append((ut["week"], ut["hours"]))

            for user_name, weeks_data in sorted(user_undertime.items()):
                result += f"**{user_name}**\n"
                for week, hours in sorted(weeks_data):
                    result += f"  Week of {week}: {hours:.2f} hours\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        # ====================================================================
        # Tool: get_user_weekly_summary
        # ====================================================================
        elif name == "get_user_weekly_summary":
            user_name = arguments["user_name"]
            weeks = arguments.get("weeks", 4)

            # Find user
            user = await client.find_user_by_name(workspace_id, user_name)
            if not user:
                return [
                    TextContent(
                        type="text", text=f"User '{user_name}' not found in workspace"
                    )
                ]

            # Calculate start date
            start_date = datetime.utcnow() - timedelta(weeks=weeks)

            # Get weekly hours
            weekly_hours = await client.calculate_weekly_hours(
                workspace_id=workspace_id, user_id=user["id"], start_date=start_date
            )

            result = f"Weekly summary for {user['name']} ({user['email']})\n"
            result += f"Past {weeks} weeks\n\n"

            total_hours = 0
            for week in sorted(weekly_hours.keys()):
                hours = weekly_hours[week]
                total_hours += hours
                result += f"Week of {week}: {hours:.2f} hours\n"

            avg_hours = total_hours / max(len(weekly_hours), 1)
            result += f"\nTotal: {total_hours:.2f} hours\n"
            result += f"Average: {avg_hours:.2f} hours/week\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run():
    """Synchronous entry point"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
