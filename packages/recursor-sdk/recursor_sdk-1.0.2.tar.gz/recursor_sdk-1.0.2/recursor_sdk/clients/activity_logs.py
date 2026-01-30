from typing import Any, Dict, Optional

class ActivityLogClientMixin:
    """Mixin for Activity Log operations"""

    def list_activity_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List activity logs with pagination and filtering
        
        Args:
            limit: Maximum number of logs to return (default: 50, max: 100)
            offset: Number of logs to skip (for pagination)
            resource_type: Filter by resource type
            action: Filter by action
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
        """
        params: Dict[str, Any] = {
            "limit": max(1, min(limit, 100)),
            "offset": max(0, offset)
        }
        if resource_type:
            params["resource_type"] = resource_type
        if action:
            params["action"] = action
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._get("/client/activity", params)

    def export_activity_logs(
        self,
        format: str = "csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Any:
        """
        Export activity logs as CSV or JSON
        """
        params: Dict[str, Any] = {"format": format}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Direct client access needed for binary/streaming content
        resp = self._client.get(
            self._url("/client/activity/export"),
            headers=self._headers,
            params=params
        )
        resp.raise_for_status()
        
        if format == "csv":
            return resp.content
        return resp.json()
