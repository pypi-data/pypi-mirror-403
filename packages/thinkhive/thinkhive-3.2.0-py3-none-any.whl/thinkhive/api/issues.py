"""
Issues API Client
ITIL-aligned terminology for clustered failure patterns

Per industry best practices, "Issues" is more customer-friendly than "Cases"
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from ..client import api_request


class IssuesClient:
    """
    Issues API client

    This is the recommended API for managing clustered failure patterns.
    """

    def list(
        self,
        agent_id: str,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List issues for an agent

        Args:
            agent_id: The agent ID to fetch issues for
            status: Filter by status (open, proposed_fix, testing, resolved, closed)
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of issues
        """
        params = {"agentId": agent_id}
        if status:
            params["status"] = status
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()
        if limit:
            params["limit"] = str(limit)
        if offset:
            params["offset"] = str(offset)

        response = api_request("GET", "/issues", params=params, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def get(self, issue_id: str) -> Dict[str, Any]:
        """
        Get a single issue by ID

        Args:
            issue_id: The issue ID

        Returns:
            Issue details
        """
        response = api_request("GET", f"/issues/{issue_id}", api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def create(
        self,
        agent_id: str,
        title: str,
        issue_type: str,
        description: Optional[str] = None,
        severity: Optional[str] = None,
        pattern: Optional[str] = None,
        example_trace_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue

        Args:
            agent_id: The agent ID
            title: Issue title
            issue_type: Type (hallucination, retrieval_miss, tone, policy, tool_failure, drift, other)
            description: Issue description
            severity: Severity level (low, medium, high, critical)
            pattern: Pattern description
            example_trace_ids: List of example trace IDs

        Returns:
            Created issue
        """
        data = {
            "agentId": agent_id,
            "title": title,
            "type": issue_type,
        }
        if description:
            data["description"] = description
        if severity:
            data["severity"] = severity
        if pattern:
            data["pattern"] = pattern
        if example_trace_ids:
            data["exampleTraceIds"] = example_trace_ids

        response = api_request("POST", "/issues", body=data, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def update(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        assigned_to: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an issue

        Args:
            issue_id: The issue ID
            title: New title
            description: New description
            status: New status
            severity: New severity
            assigned_to: User ID to assign to
            resolution_notes: Resolution notes

        Returns:
            Updated issue
        """
        data = {}
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if status:
            data["status"] = status
        if severity:
            data["severity"] = severity
        if assigned_to:
            data["assignedTo"] = assigned_to
        if resolution_notes:
            data["resolutionNotes"] = resolution_notes

        response = api_request("PATCH", f"/issues/{issue_id}", body=data, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def get_fixes(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        Get fixes for an issue

        Args:
            issue_id: The issue ID

        Returns:
            List of fixes
        """
        response = api_request("GET", f"/issues/{issue_id}/fixes", api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response


# Singleton instance
issues = IssuesClient()
