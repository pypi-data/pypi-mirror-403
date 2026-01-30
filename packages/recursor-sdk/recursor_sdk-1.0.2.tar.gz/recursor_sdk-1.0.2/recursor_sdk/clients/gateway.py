from typing import Any, Dict, List, Optional

class GatewayClientMixin:
    """Mixin for AI Gateway operations"""

    def get_llm_gateway_policy(self) -> Dict[str, Any]:
        """Get LLM gateway policy"""
        return self._get("/recursor/llm/gateway/policy")

    def gateway_chat(
        self,
        messages: List[Dict[str, str]],
        provider: str = "gradient",
        model: Optional[str] = None,
        call_provider: bool = True,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """LLM gateway chat"""
        payload = {
            "provider": provider,
            "model": model,
            "messages": messages,
            "call_provider": call_provider,
            "user_id": user_id,
        }
        return self._post("/recursor/llm/gateway/chat", payload)

    def get_robotics_gateway_policy(self) -> Dict[str, Any]:
        """Get robotics gateway policy"""
        return self._get("/recursor/robotics/gateway/policy")

    def robotics_gateway_observe(
        self,
        state: Dict[str, Any],
        command: Optional[Dict[str, Any]] = None,
        environment: Optional[List[Dict[str, Any]]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Robotics gateway observe"""
        payload = {
            "state": state,
            "command": command,
            "environment": environment or [],
            "user_id": user_id,
        }
        return self._post("/recursor/robotics/gateway/observe", payload)

    def get_av_gateway_policy(self) -> Dict[str, Any]:
        """Get AV gateway policy"""
        return self._get("/recursor/av/gateway/policy")

    def av_gateway_observe(
        self,
        sensors: Dict[str, Any],
        state: Dict[str, Any],
        action: Dict[str, Any],
        timestamp: int,
        vehicle_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """AV gateway observe"""
        payload = {
            "sensors": sensors,
            "state": state,
            "action": action,
            "timestamp": timestamp,
            "vehicle_id": vehicle_id,
            "user_id": user_id,
        }
        return self._post("/recursor/av/gateway/observe", payload)
