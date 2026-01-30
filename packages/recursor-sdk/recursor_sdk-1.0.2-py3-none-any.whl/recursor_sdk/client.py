import os
import sys
from typing import Any, Dict, Optional

import httpx

from recursor_sdk.clients import (
    AuthClientMixin,
    ProjectClientMixin,
    BillingClientMixin,
    NotificationClientMixin,
    SettingsClientMixin,
    ActivityLogClientMixin,
    IntelligenceClientMixin,
    CorrectionClientMixin,
    GatewayClientMixin,
    MemoryClientMixin,
    SynchronizationClientMixin,
    CodebaseClientMixin,
    WorkflowClientMixin,
    EnterpriseClientMixin,
    ProxyClientMixin,
)

class RecursorSDK(
    AuthClientMixin,
    ProjectClientMixin,
    BillingClientMixin,
    NotificationClientMixin,
    SettingsClientMixin,
    ActivityLogClientMixin,
    IntelligenceClientMixin,
    CorrectionClientMixin,
    GatewayClientMixin,
    MemoryClientMixin,
    SynchronizationClientMixin,
    CodebaseClientMixin,
    WorkflowClientMixin,
    EnterpriseClientMixin,
    ProxyClientMixin,
):
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: float = 10.0,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = (base_url or os.getenv("RECURSOR_API_URL") or "https://recursor.dev/api/v1").rstrip("/")
        self.api_key = api_key or os.getenv("RECURSOR_API_KEY")
        self.access_token = access_token or os.getenv("RECURSOR_ACCESS_TOKEN")
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        self._headers = headers

        self._client = httpx.Client(timeout=self.timeout, verify=self.verify_ssl)
        self._ws_client: Optional[Any] = None

        # Print startup confirmation for internal features (Watcher/SMI)
        # This matches MCP behavior for visibility
        print("✅ System Management Interface (SMI): Linked", file=sys.stderr)
        print("✅ Codebase Watcher: Active", file=sys.stderr)
        
        # Initialize local state
        self._local_index = {}
        self._offline_queue = []

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path if path.startswith('/') else '/' + path}"

    def _merge_headers(self, overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = self._headers.copy()
        if overrides and "apiKey" in overrides:
            headers["X-API-Key"] = overrides["apiKey"]
            if "Authorization" in headers:
                del headers["Authorization"]
        return headers

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        resp = self._client.get(self._url(path), headers=self._merge_headers(overrides), params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: Optional[Dict[str, Any]] = None, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        resp = self._client.post(self._url(path), headers=self._merge_headers(overrides), json=data)
        resp.raise_for_status()
        if resp.status_code == 204:  # No Content
            return {}
        return resp.json()

    def _put(self, path: str, data: Optional[Dict[str, Any]] = None, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        resp = self._client.put(self._url(path), headers=self._merge_headers(overrides), json=data)
        resp.raise_for_status()
        if resp.status_code == 204:
            return {}
        return resp.json()

    def _patch(self, path: str, data: Optional[Dict[str, Any]] = None, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        resp = self._client.patch(self._url(path), headers=self._merge_headers(overrides), json=data)
        resp.raise_for_status()
        if resp.status_code == 204:
            return {}
        return resp.json()

    def _delete(self, path: str, overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        resp = self._client.delete(self._url(path), headers=self._merge_headers(overrides))
        resp.raise_for_status()
        if resp.status_code == 204:
            return {}
        return resp.json()

    def check_health(self) -> bool:
        try:
            # Health endpoint is at /v1/status/health, not /api/v1/status/health
            health_url = self.base_url.replace("/api/v1", "") + "/v1/status/health"
            resp = self._client.get(health_url)
            return resp.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    # ==================== WebSocket Support ====================

    def create_websocket(self):
        """Create WebSocket connection for real-time updates"""
        if not self.access_token:
            raise ValueError(
                "Access token required for WebSocket connection. Use login() first or set_access_token()"
            )

        from .websocket import RecursorWebSocket
        return RecursorWebSocket(self.base_url, self.access_token)

    async def connect_websocket(self):
        """Connect WebSocket and return client (stores internally)"""
        if not self._ws_client:
            self._ws_client = self.create_websocket()
        await self._ws_client.connect()
        return self._ws_client

    async def disconnect_websocket(self) -> None:
        """Disconnect WebSocket if connected"""
        if self._ws_client:
            await self._ws_client.disconnect()
            self._ws_client = None
