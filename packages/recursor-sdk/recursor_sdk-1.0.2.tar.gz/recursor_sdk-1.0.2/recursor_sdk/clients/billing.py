from typing import Any, Dict, List, Optional

class BillingClientMixin:
    """Mixin for Billing & Usage operations"""

    def get_usage(self, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self._get("/client/billing/usage", overrides=overrides)

    def get_usage_history(
        self, 
        days: int = 30, 
        resource_type: Optional[str] = None,
        overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get usage history"""
        params = {"days": days}
        if resource_type:
            params["resource_type"] = resource_type
        return self._get("/client/billing/usage/history", params, overrides=overrides)

    def list_billing_plans(self, overrides: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """List available billing plans"""
        data = self._get("/client/billing/plans", overrides=overrides)
        return data.get("plans", []) if isinstance(data, dict) else []

    def get_subscription(self, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get current subscription"""
        return self._get("/client/billing/subscription", overrides=overrides)
