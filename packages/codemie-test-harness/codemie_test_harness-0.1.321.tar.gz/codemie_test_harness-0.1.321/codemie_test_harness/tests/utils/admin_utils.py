"""Admin utilities for managing applications/projects."""

from typing import Optional, List

from codemie_sdk.models.admin import ApplicationCreateRequest

from codemie_test_harness.tests.utils.base_utils import BaseUtils


class AdminUtils(BaseUtils):
    """Utility class for admin operations on applications/projects."""

    def list_projects(self, name_filter: Optional[str] = None) -> List[str]:
        """Get list of all projects/applications.

        Args:
            name_filter: Optional project name to filter by

        Returns:
            List of application names
        """
        return self.client.admin.list_applications(project_name=name_filter)

    def create_project(self, project_name: str) -> str:
        """Create a new project/application.

        Args:
            project_name: Name of the project to create

        Returns:
            Created application name
        """
        request = ApplicationCreateRequest(name=project_name)
        return self.client.admin.create_application(request)
