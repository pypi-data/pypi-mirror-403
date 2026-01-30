from typing import Any, Dict, List, Optional

class ProjectClientMixin:
    """Mixin for Project Management operations"""

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new project"""
        payload = {
            "name": name,
            "description": description,
            "settings": settings or {},
        }
        return self._post("/client/projects", payload)

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project by ID"""
        return self._get(f"/client/projects/{project_id}")

    def list_projects(self) -> List[Dict[str, Any]]:
        """List current user projects"""
        data = self._get("/client/projects")
        return data if isinstance(data, list) else []

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update project"""
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if settings is not None:
            payload["settings"] = settings
        if is_active is not None:
            payload["is_active"] = is_active
        return self._patch(f"/client/projects/{project_id}", payload)

    def delete_project(self, project_id: str) -> None:
        """Delete project"""
        self._delete(f"/client/projects/{project_id}")

    def regenerate_project_api_key(self, project_id: str) -> Dict[str, Any]:
        """Regenerate project API key"""
        return self._post(f"/client/projects/{project_id}/api-key", {})

    def get_mcp_config(self, project_id: str) -> Dict[str, Any]:
        """Get MCP configuration for project"""
        return self._get(f"/client/projects/{project_id}/mcp-config")

    def get_mcp_stats(self, project_id: str) -> Dict[str, Any]:
        """Get MCP usage statistics for project"""
        return self._get(f"/client/projects/{project_id}/mcp-stats")
