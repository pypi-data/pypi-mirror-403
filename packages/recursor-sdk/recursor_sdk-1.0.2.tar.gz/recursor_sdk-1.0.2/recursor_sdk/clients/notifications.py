from typing import Any, Dict, List

class NotificationClientMixin:
    """Mixin for Notification operations"""

    def list_notifications(self) -> List[Dict[str, Any]]:
        """List notifications"""
        data = self._get("/client/notifications")
        return data.get("notifications", []) if isinstance(data, dict) else []

    def mark_notification_as_read(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as read"""
        return self._post(f"/client/notifications/{notification_id}/read", {})

    def mark_all_notifications_as_read(self) -> None:
        """Mark all notifications as read"""
        self._post("/client/notifications/read-all", {})

    def delete_notification(self, notification_id: str) -> None:
        """Delete notification"""
        self._delete(f"/client/notifications/{notification_id}")
