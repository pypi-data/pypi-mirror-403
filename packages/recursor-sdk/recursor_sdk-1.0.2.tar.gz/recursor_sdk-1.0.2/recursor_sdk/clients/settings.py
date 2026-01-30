from typing import Any, Dict, Optional

class SettingsClientMixin:
    """Mixin for User Settings operations"""

    def get_settings(self) -> Dict[str, Any]:
        """Get user settings"""
        return self._get("/client/settings")

    def update_account(self, full_name: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """Update account information"""
        payload = {}
        if full_name is not None:
            payload["full_name"] = full_name
        if email is not None:
            payload["email"] = email
        return self._put("/client/settings/account", payload)

    def update_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        return self._put("/client/settings/preferences", preferences)

    def get_guidelines(self) -> Dict[str, Any]:
        """Get coding guidelines"""
        return self._get("/client/settings/guidelines")

    def change_password_via_settings(self, current_password: str, new_password: str) -> None:
        """Change password via settings"""
        self._put("/client/settings/password", {
            "current_password": current_password,
            "new_password": new_password,
        })

    def delete_account(self) -> None:
        """Delete user account"""
        self._delete("/client/settings/account")
