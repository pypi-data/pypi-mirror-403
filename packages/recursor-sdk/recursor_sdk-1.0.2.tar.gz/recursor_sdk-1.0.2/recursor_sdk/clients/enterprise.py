"""
Enterprise service client mixin
"""

from typing import Any, Dict, List, Optional


class EnterpriseClientMixin:
    """Enterprise service client mixin"""

    def get_user_audit_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit logs for the current user
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            action: Filter by action type
            
        Returns:
            Dictionary containing logs and metadata
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        if action:
            params["action"] = action
            
        return self._get("/client/audit/audit-logs", params=params)
