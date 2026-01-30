from typing import Any, Dict, List, Optional
from uuid import UUID

class WorkflowClientMixin:
    """Mixin for AI Workflow management operations"""

    def create_workflow(
        self,
        name: str,
        definition: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new AI workflow definition"""
        payload = {
            "name": name,
            "definition": definition,
            "description": description
        }
        return self._post("/client/workflows/", payload)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List AI workflows available to the user"""
        return self._get("/client/workflows/")

    def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger an execution of a specific workflow"""
        return self._post(f"/client/workflows/{workflow_id}/execute", input_data)

    def get_execution_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """Get the current status and results of a workflow execution"""
        return self._get(f"/client/workflows/executions/{execution_id}")
