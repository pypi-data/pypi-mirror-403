"""Admin service implementation."""

from typing import List, Optional

from ..models.admin import (
    ApplicationsListResponse,
    ApplicationCreateRequest,
    ApplicationCreateResponse,
)
from ..utils import ApiRequestHandler


class AdminService:
    """Service for managing CodeMie applications/projects."""

    def __init__(self, api_domain: str, token: str, verify_ssl: bool = True):
        """Initialize the admin service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def list_applications(self, project_name: Optional[str] = None) -> List[str]:
        """Get list of all applications/projects.

        Args:
            project_name: Optional project name to filter by

        Returns:
            List of application names
        """
        params = {}
        if project_name:
            params["search"] = project_name

        response = self._api.get(
            "/v1/admin/applications",
            ApplicationsListResponse,
            params=params if params else None,
        )
        return response.applications

    def create_application(self, request: ApplicationCreateRequest) -> str:
        """Create a new application/project.

        Args:
            request: Application creation request

        Returns:
            Created application name
        """
        response = self._api.post(
            "/v1/admin/application",
            ApplicationCreateResponse,
            json_data=request.model_dump(exclude_none=True),
        )
        return response.message
