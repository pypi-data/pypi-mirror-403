from typing import Any, Dict, Optional

class AuthClientMixin:
    """Mixin for Authentication & User Management operations"""
    
    def set_access_token(self, token: str) -> None:
        """Set access token for authenticated requests"""
        self.access_token = token
        self._headers["Authorization"] = f"Bearer {token}"
        if "X-API-Key" in self._headers:
            del self._headers["X-API-Key"]

    def set_api_key(self, key: str) -> None:
        """Set API key for authenticated requests"""
        self.api_key = key
        self._headers["X-API-Key"] = key
        if "Authorization" in self._headers:
            del self._headers["Authorization"]

    def register(
        self,
        email: str,
        password: str,
        username: str,
        full_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new user"""
        payload = {
            "email": email,
            "password": password,
            "username": username,
            "full_name": full_name,
        }
        return self._post("/client/auth/register", payload)

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get access token"""
        payload = {"email": email, "password": password}
        response = self._post("/client/auth/login", payload)
        # Automatically set access token
        if "access_token" in response:
            self.set_access_token(response["access_token"])
            # Update WebSocket token if connected
            if hasattr(self, "_ws_client") and self._ws_client:
                self._ws_client.update_token(response["access_token"])
        return response

    def logout(self) -> None:
        """Logout current user"""
        self._post("/client/auth/logout", {})

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        response = self._post("/client/auth/refresh", {"refresh_token": refresh_token})
        if "access_token" in response:
            self.set_access_token(response["access_token"])
        return response

    def get_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        return self._get("/client/auth/me")

    def update_profile(self, full_name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
        """Update user profile"""
        payload = {}
        if full_name is not None:
            payload["full_name"] = full_name
        if username is not None:
            payload["username"] = username
        return self._put("/client/auth/me", payload)

    def change_password(self, current_password: str, new_password: str) -> None:
        """Change user password"""
        self._post("/client/auth/change-password", {
            "current_password": current_password,
            "new_password": new_password,
        })

    def generate_api_key(self) -> Dict[str, Any]:
        """Generate API key for current user"""
        return self._post("/client/auth/api-key", {})

    def revoke_api_key(self) -> None:
        """Revoke current user's API key"""
        self._delete("/client/auth/api-key")

    def get_password_requirements(self) -> Dict[str, Any]:
        """Get password requirements"""
        return self._get("/client/auth/password-requirements")
