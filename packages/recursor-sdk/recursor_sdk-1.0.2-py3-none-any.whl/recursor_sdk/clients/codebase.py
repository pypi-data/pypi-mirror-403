from typing import Any, Dict, List, Optional

class CodebaseClientMixin:
    """Mixin for Codebase operations"""

    def list_codebase_files(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List files in the codebase index"""
        params = {"limit": limit, "offset": offset}
        return self._get("/client/codebase/files", params)

    def get_codebase_index(self) -> Dict[str, Any]:
        """Get the full codebase index statistics and file list"""
        return self._get("/client/codebase/index")

    def get_directory_structure(
        self,
        max_depth: int = 3,
        include_files: bool = True
    ) -> Dict[str, Any]:
        """Get the hierarchical directory structure of the codebase"""
        params = {"max_depth": max_depth, "include_files": include_files}
        return self._get("/client/codebase/structure", params)

    def validate_codebase_operation(
        self,
        action: str,
        path: str
    ) -> Dict[str, Any]:
        """Validate a file operation (create, update, delete, move) before execution"""
        payload = {"action": action, "path": path}
        return self._post("/client/codebase/validate", payload)

    def find_similar_files(
        self,
        name: str,
        threshold: float = 0.6
    ) -> List[str]:
        """Find files with similar names or content patterns"""
        params = {"name": name, "threshold": threshold}
        return self._get("/client/codebase/similar", params)
