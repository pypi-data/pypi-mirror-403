from typing import Any, Dict, Optional

class CorrectionClientMixin:
    """Mixin for Correction operations"""

    def create_correction(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        correction_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new correction"""
        payload: Dict[str, Any] = {
            "input_text": (input_text or "")[:4000],
            "output_text": (output_text or "")[:4000],
            "expected_output": (expected_output or output_text or "")[:4000],
            "context": context or {},
            "correction_type": correction_type,
        }
        return self._post("/client/corrections/", payload)

    def list_corrections(
        self,
        page: int = 1,
        page_size: int = 50,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        """List corrections"""
        params: Dict[str, Any] = {
            "page": max(1, page),
            "page_size": max(1, min(page_size, 100)),
            "include_inactive": bool(include_inactive),
        }
        return self._get("/client/corrections/", params)

    def search_corrections(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Search corrections"""
        params: Dict[str, Any] = {
            "query": (query or "").strip()[:4000],
            "limit": max(1, min(limit, 50)),
        }
        return self._get("/client/corrections/search", params)

    def get_correction(self, correction_id: str) -> Dict[str, Any]:
        """Get correction by ID"""
        return self._get(f"/client/corrections/{correction_id}")

    def update_correction(self, correction_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update correction"""
        return self._put(f"/client/corrections/{correction_id}", updates)

    def get_correction_stats(self) -> Dict[str, Any]:
        """Get correction statistics"""
        return self._get("/client/corrections/stats")
