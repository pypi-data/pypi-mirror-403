"""
Clockify API Client for MCP Server
Provides high-level interface to Clockify API
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ClockifyClient:
    """Client for interacting with Clockify API"""

    def __init__(self, api_key: str, base_url: str = "https://api.clockify.me/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.reports_base_url = "https://reports.api.clockify.me/v1"
        self.headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    # ============================================================================
    # User Operations
    # ============================================================================

    async def get_current_user(self) -> Dict[str, Any]:
        """Get currently logged-in user's info"""
        url = f"{self.base_url}/user"
        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def get_workspace_users(
        self,
        workspace_id: str,
        status: str = "ACTIVE",
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all users in a workspace with optional filtering"""
        url = f"{self.base_url}/workspaces/{workspace_id}/users"
        params = {"status": status, "page-size": 1000}

        if name:
            params["name"] = name
        if email:
            params["email"] = email

        response = await self.client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    async def find_user_by_name(
        self, workspace_id: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Find a user by name (prefers exact match, falls back to partial)"""
        users = await self.get_workspace_users(workspace_id, name=name)

        name_lower = name.lower()

        # First, look for exact match
        for user in users:
            if user.get("name", "").lower() == name_lower:
                return user

        # Fall back to partial match
        for user in users:
            if name_lower in user.get("name", "").lower():
                return user

        return None

    # ============================================================================
    # Workspace Operations
    # ============================================================================

    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all workspaces for current user"""
        url = f"{self.base_url}/workspaces"
        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def get_default_workspace(self) -> Dict[str, Any]:
        """Get the user's default workspace"""
        user = await self.get_current_user()
        workspace_id = user.get("defaultWorkspace")

        if not workspace_id:
            # Get first workspace if no default
            workspaces = await self.get_workspaces()
            if workspaces:
                return workspaces[0]
            raise ValueError("No workspaces found")

        workspaces = await self.get_workspaces()
        for ws in workspaces:
            if ws["id"] == workspace_id:
                return ws

        raise ValueError(f"Default workspace {workspace_id} not found")

    # ============================================================================
    # Project Operations
    # ============================================================================

    async def get_projects(
        self, workspace_id: str, archived: bool = False, name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all projects in a workspace"""
        url = f"{self.base_url}/workspaces/{workspace_id}/projects"
        params = {"archived": str(archived).lower(), "page-size": 1000}

        if name:
            params["name"] = name

        response = await self.client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    async def find_project_by_name(
        self, workspace_id: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Find a project by name (prefers exact match, falls back to partial)"""
        projects = await self.get_projects(workspace_id, name=name)

        name_lower = name.lower()

        # First, look for exact match
        for project in projects:
            if project.get("name", "").lower() == name_lower:
                return project

        # Fall back to partial match
        for project in projects:
            if name_lower in project.get("name", "").lower():
                return project

        return None

    # ============================================================================
    # Task Operations
    # ============================================================================

    async def get_project_tasks(
        self,
        workspace_id: str,
        project_id: str,
        is_active: bool = True,
        name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        url = f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}/tasks"
        params = {"page-size": 1000, "is-active": str(is_active).lower()}

        if name:
            params["name"] = name

        response = await self.client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    async def find_task_by_name(
        self, workspace_id: str, project_id: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Find a task by name within a project (prefers exact match, falls back to partial)"""
        tasks = await self.get_project_tasks(workspace_id, project_id, name=name)

        name_lower = name.lower()

        # First, look for exact match
        for task in tasks:
            if task.get("name", "").lower() == name_lower:
                return task

        # Fall back to partial match
        for task in tasks:
            if name_lower in task.get("name", "").lower():
                return task

        return None

    # ============================================================================
    # Time Entry Operations
    # ============================================================================

    async def get_time_entries(
        self,
        workspace_id: str,
        user_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get time entries for a user with optional filtering"""
        url = f"{self.base_url}/workspaces/{workspace_id}/user/{user_id}/time-entries"

        params = {"page-size": 1000, "hydrated": "true"}

        if start:
            params["start"] = start.isoformat() + "Z"
        if end:
            params["end"] = end.isoformat() + "Z"
        if description:
            params["description"] = description
        if project_id:
            params["project"] = project_id

        response = await self.client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    async def search_time_entries(
        self,
        workspace_id: str,
        user_id: str,
        search_phrase: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search time entries by description phrase"""
        entries = await self.get_time_entries(
            workspace_id=workspace_id, user_id=user_id, start=start, end=end
        )

        # Filter by search phrase (case-insensitive)
        search_lower = search_phrase.lower()
        return [
            entry
            for entry in entries
            if search_lower in entry.get("description", "").lower()
        ]

    async def create_time_entry(
        self,
        workspace_id: str,
        start: datetime,
        end: Optional[datetime] = None,
        description: str = "",
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        billable: bool = True,
    ) -> Dict[str, Any]:
        """Create a new time entry"""
        url = f"{self.base_url}/workspaces/{workspace_id}/time-entries"

        payload = {
            "start": start.isoformat() + "Z",
            "billable": billable,
            "description": description,
        }

        if end:
            payload["end"] = end.isoformat() + "Z"
        if project_id:
            payload["projectId"] = project_id
        if task_id:
            payload["taskId"] = task_id

        response = await self.client.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def start_timer(
        self,
        workspace_id: str,
        description: str = "",
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start a new timer (time entry without end time)"""
        return await self.create_time_entry(
            workspace_id=workspace_id,
            start=datetime.utcnow(),
            end=None,
            description=description,
            project_id=project_id,
            task_id=task_id,
        )

    async def stop_timer(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """Stop currently running timer"""
        url = f"{self.base_url}/workspaces/{workspace_id}/user/{user_id}/time-entries"

        payload = {"end": datetime.utcnow().isoformat() + "Z"}

        response = await self.client.patch(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def get_running_timer(
        self, workspace_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get currently running timer for a user"""
        url = f"{self.base_url}/workspaces/{workspace_id}/user/{user_id}/time-entries"
        params = {"in-progress": "true"}

        response = await self.client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        entries = response.json()

        return entries[0] if entries else None

    # ============================================================================
    # Project Time Entry Operations
    # ============================================================================

    async def get_project_time_entries(
        self,
        workspace_id: str,
        project_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all time entries for a project by fetching entries from all users.

        This uses the standard Time Entry API (which supports project filtering)
        instead of the Reports API (which requires a paid plan).
        """
        # Get all active users in the workspace
        users = await self.get_workspace_users(workspace_id)

        all_entries = []

        for user in users:
            try:
                entries = await self.get_time_entries(
                    workspace_id=workspace_id,
                    user_id=user["id"],
                    start=start,
                    end=end,
                    project_id=project_id,
                )

                # Add user info to each entry for later display
                for entry in entries:
                    entry["_user"] = {
                        "id": user["id"],
                        "name": user.get("name", "Unknown"),
                        "email": user.get("email", ""),
                    }

                all_entries.extend(entries)
            except Exception as e:
                # Log but continue if a single user fails
                logger.warning(
                    f"Failed to get entries for user {user.get('name')}: {e}"
                )
                continue

        # Sort by start time (most recent first)
        all_entries.sort(
            key=lambda x: x.get("timeInterval", {}).get("start", ""), reverse=True
        )

        return all_entries

    # ============================================================================
    # Reporting Operations (requires paid plan)
    # ============================================================================

    async def get_detailed_report(
        self,
        workspace_id: str,
        start: datetime,
        end: datetime,
        user_ids: Optional[List[str]] = None,
        project_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get detailed time entry report"""
        url = f"{self.reports_base_url}/workspaces/{workspace_id}/reports/detailed"

        payload = {
            "dateRangeStart": start.isoformat() + "Z",
            "dateRangeEnd": end.isoformat() + "Z",
            "detailedFilter": {
                "page": 1,
                "pageSize": 1000,
                "sortColumn": "DATE",
                "sortOrder": "DESCENDING",
                "options": {"totals": "CALCULATE", "includeTimeEntries": True},
            },
            "amountShown": "EARNED",
            "exportType": "JSON",
        }

        if user_ids:
            payload["detailedFilter"]["users"] = {
                "ids": user_ids,
                "contains": "CONTAINS",
                "status": "ACTIVE",
            }

        if project_ids:
            payload["detailedFilter"]["projects"] = {
                "ids": project_ids,
                "contains": "CONTAINS",
                "status": "ACTIVE",
            }

        response = await self.client.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    # ============================================================================
    # Helper Functions
    # ============================================================================

    @staticmethod
    def parse_duration_to_hours(duration_str: str) -> float:
        """
        Parse ISO 8601 duration format to decimal hours.
        Handles: PT3036S, PT1H30M, PT1H30M45S, PT30M, PT1H, etc.
        """
        if not duration_str or duration_str == "PT0S":
            return 0.0

        # Remove PT prefix
        remaining = duration_str.replace("PT", "")

        hours = 0
        minutes = 0
        seconds = 0

        # Parse hours (if present)
        if "H" in remaining:
            hours_str, remaining = remaining.split("H", 1)
            hours = int(hours_str)

        # Parse minutes (if present)
        if "M" in remaining:
            minutes_str, remaining = remaining.split("M", 1)
            minutes = int(minutes_str)

        # Parse seconds (if present)
        if "S" in remaining:
            seconds_str = remaining.replace("S", "")
            if seconds_str:  # Not empty
                seconds = int(seconds_str)

        # Convert everything to hours
        return hours + (minutes / 60.0) + (seconds / 3600.0)

    @staticmethod
    def seconds_to_hours(seconds: int) -> float:
        """Convert seconds to hours"""
        return seconds / 3600

    async def calculate_weekly_hours(
        self,
        workspace_id: str,
        user_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """Calculate hours for each week in the given period"""
        # Default end_date to now if not provided
        if end_date is None:
            end_date = datetime.utcnow()

        entries = await self.get_time_entries(
            workspace_id=workspace_id, user_id=user_id, start=start_date, end=end_date
        )

        # Group by week
        weekly_hours = {}

        for entry in entries:
            time_interval = entry.get("timeInterval", {})
            duration = time_interval.get("duration", "PT0S")
            hours = self.parse_duration_to_hours(duration)

            # Determine week
            entry_start = datetime.fromisoformat(
                time_interval["start"].replace("Z", "+00:00")
            )
            week_start = entry_start - timedelta(days=entry_start.weekday())
            week_key = week_start.strftime("%Y-%m-%d")

            weekly_hours[week_key] = weekly_hours.get(week_key, 0.0) + hours

        return weekly_hours
