from typing import Any, Dict, List, Optional

class MemoryClientMixin:
    """Mixin for Memory & Rotatable Memory operations"""

    def create_conversation_summary(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        summary_text: str,
        key_points: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a conversation summary"""
        payload = {
            "conversation_id": conversation_id,
            "messages": messages,
            "summary_text": summary_text,
            "key_points": key_points or [],
            "topics": topics or [],
            "metadata": metadata or {},
        }
        return self._post("/client/memory/conversations/summaries", payload)

    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a conversation summary by ID"""
        return self._get(f"/client/memory/conversations/summaries/{conversation_id}")

    def list_conversation_summaries(
        self,
        limit: int = 10,
        days: int = 7,
    ) -> Dict[str, Any]:
        """List recent conversation summaries"""
        params = {"limit": limit, "days": days}
        return self._get("/client/memory/conversations/summaries", params)

    def record_architectural_change(
        self,
        change_type: str,
        component: str,
        description: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        impact: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an architectural change"""
        payload = {
            "change_type": change_type,
            "component": component,
            "description": description,
            "before": before,
            "after": after,
            "impact": impact or [],
            "metadata": metadata or {},
        }
        return self._post("/client/memory/architectural/changes", payload)

    def list_architectural_changes(
        self,
        limit: int = 20,
        days: int = 30,
        change_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List recent architectural changes"""
        params = {"limit": limit, "days": days}
        if change_type:
            params["change_type"] = change_type
        return self._get("/client/memory/architectural/changes", params)

    def query_rotatable_memory(
        self,
        domain: Optional[str] = None,
        pattern_type: Optional[str] = None,
        min_effectiveness: Optional[float] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Query rotatable memory patterns"""
        payload = {}
        if domain:
            payload["domain"] = domain
        if pattern_type:
            payload["pattern_type"] = pattern_type
        if min_effectiveness is not None:
            payload["min_effectiveness"] = min_effectiveness
        payload["limit"] = limit
        return self._post("/client/memory/rotatable/query", payload)

    def record_pattern_usage(self, pattern_id: str, successful: bool) -> Dict[str, Any]:
        """Record pattern usage and update effectiveness"""
        payload = {
            "pattern_id": pattern_id,
            "successful": successful,
        }
        return self._post("/client/memory/rotatable/usage", payload)

    def get_rotatable_memory_stats(self) -> Dict[str, Any]:
        """Get rotatable memory statistics"""
        return self._get("/client/memory/rotatable/stats")
