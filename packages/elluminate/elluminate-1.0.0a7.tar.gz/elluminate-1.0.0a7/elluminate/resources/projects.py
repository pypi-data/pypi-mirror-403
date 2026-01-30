from __future__ import annotations

import httpx

from elluminate.resources.base import BaseResource
from elluminate.schemas import Project
from elluminate.utils import raise_for_status_with_detail


class ProjectsResource(BaseResource):
    def load_project(self, project_id: int | None = None, *, url: str | None = None) -> Project:
        """Synchronously load and select the active project."""
        projects = self.list_projects(url=url)
        target_project_id = self._resolve_target_project_id(projects, project_id)
        # Find the project in our list instead of making another API call
        selected_project = next((p for p in projects if p.id == target_project_id), None)
        if selected_project is None:
            raise RuntimeError(
                f"Project with ID {target_project_id} not found in available projects. "
                f"Available project IDs: {[p.id for p in projects]}"
            )
        return self._set_active_project(selected_project)

    def list_projects(self, *, url: str | None = None) -> list[Project]:
        """List all projects accessible to the current credentials."""
        list_url = url or f"{self._client.base_url}/api/v0/projects"
        response = self._client.sync_session.get(list_url)
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "No project found (404). Please double check that your base_url and credentials are set correctly (also check your environment variables ELLUMINATE_API_KEY / ELLUMINATE_OAUTH_TOKEN and ELLUMINATE_BASE_URL).",
                request=response.request,
                response=response,
            )
        raise_for_status_with_detail(response)
        return [Project.model_validate(project) for project in response.json().get("items", [])]

    def select_project(self, project_id: int) -> Project:
        """Select a specific project and update the client state."""
        response = self._client.sync_session.get(self._project_url(project_id))
        raise_for_status_with_detail(response)
        return self._set_active_project(Project.model_validate(response.json()))

    def _resolve_target_project_id(self, projects: list[Project], project_id: int | None) -> int:
        if not projects:
            raise RuntimeError("No projects found.")

        if self._client.api_key:
            return projects[0].id  # for API key auth, there is always only one project

        if project_id is not None:
            return project_id

        return max(
            projects, key=lambda project: project.id
        ).id  # for Oauth token auth, we default to the newest project by id

    def _set_active_project(self, project: Project) -> Project:
        self._client.current_project = project
        self._client.project_route_prefix = f"{self._client.base_url}/api/v0/projects/{project.id}"
        return project

    def _project_url(self, project_id: int) -> str:
        return f"{self._client.base_url}/api/v0/projects/{project_id}"

    def create(self, name: str, description: str = "") -> Project:
        """Create a new project.

        Args:
            name: Name of the project (must be unique)
            description: Optional description of the project

        Returns:
            The created Project object

        """
        # Use base URL directly, not project-scoped route
        create_url = f"{self._client.base_url}/api/v0/projects"
        response = self._client.sync_session.post(
            create_url,
            json={
                "name": name,
                "description": description,
                "organization_id": self._client.current_project.organization.id,
            },
        )
        raise_for_status_with_detail(response)
        return Project.model_validate(response.json())

    # ===== Async Methods =====

    async def aload_project(self, project_id: int | None = None, *, url: str | None = None) -> Project:
        """Asynchronously load and select the active project."""
        projects = await self.alist_projects(url=url)
        target_project_id = self._resolve_target_project_id(projects, project_id)
        # Find the project in our list instead of making another API call
        selected_project = next((p for p in projects if p.id == target_project_id), None)
        if selected_project is None:
            raise RuntimeError(
                f"Project with ID {target_project_id} not found in available projects. "
                f"Available project IDs: {[p.id for p in projects]}"
            )
        return self._set_active_project(selected_project)

    async def alist_projects(self, *, url: str | None = None) -> list[Project]:
        """List all projects accessible to the current credentials (async)."""
        list_url = url or f"{self._client.base_url}/api/v0/projects"
        response = await self._client.async_session.get(list_url)
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "No project found (404). Please double check that your base_url and credentials are set correctly (also check your environment variables ELLUMINATE_API_KEY / ELLUMINATE_OAUTH_TOKEN and ELLUMINATE_BASE_URL).",
                request=response.request,
                response=response,
            )
        raise_for_status_with_detail(response)
        return [Project.model_validate(project) for project in response.json().get("items", [])]

    async def aselect_project(self, project_id: int) -> Project:
        """Select a specific project and update the client state (async)."""
        response = await self._client.async_session.get(self._project_url(project_id))
        raise_for_status_with_detail(response)
        return self._set_active_project(Project.model_validate(response.json()))

    async def acreate(self, name: str, description: str = "") -> Project:
        """Create a new project (async).

        Args:
            name: Name of the project (must be unique)
            description: Optional description of the project

        Returns:
            The created Project object

        """
        # Use base URL directly, not project-scoped route
        create_url = f"{self._client.base_url}/api/v0/projects"
        response = await self._client.async_session.post(
            create_url,
            json={
                "name": name,
                "description": description,
                "organization_id": self._client.current_project.organization.id,
            },
        )
        raise_for_status_with_detail(response)
        return Project.model_validate(response.json())
