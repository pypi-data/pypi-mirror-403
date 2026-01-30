from typing import Any, Dict, List, Optional

class IntelligenceClientMixin:
    """Mixin for Code Intelligence & Analytics operations"""

    def detect_intent(
        self,
        user_request: str,
        current_file: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        similar_limit: Optional[int] = 5,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "user_request": (user_request or "").strip()[:4000],
            "current_file": current_file,
            "user_id": user_id,
            "project_id": project_id,
            "tags": tags or [],
            "similar_limit": similar_limit,
        }
        return self._post("/client/code_intelligence/detect-intent", payload, overrides=overrides)

    def get_intent_history(
        self,
        limit: int = 50,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": max(1, min(limit, 200))}
        if project_id:
            params["project_id"] = project_id
        data = self._get("/client/code_intelligence/intent-history", params)
        return data if isinstance(data, list) else []

    def get_analytics_dashboard(
        self,
        user_id: str,
        period: str = "30d",
        project_id: Optional[str] = None,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"user_id": user_id, "period": period}
        if project_id:
            params["project_id"] = project_id
        return self._get("/client/code_intelligence/analytics/dashboard", params, overrides=overrides)

    def get_time_saved(
        self,
        user_id: str,
        period: str = "30d", 
        project_id: Optional[str] = None,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"user_id": user_id, "period": period}
        if project_id:
            params["project_id"] = project_id
        return self._get("/client/code_intelligence/analytics/time-saved", params, overrides=overrides)

    def get_quality_metrics(
        self,
        user_id: str,
        period: str = "30d",
        project_id: Optional[str] = None,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"user_id": user_id, "period": period}
        if project_id:
            params["project_id"] = project_id
        return self._get("/client/code_intelligence/analytics/quality", params, overrides=overrides)

    def get_ai_agent_metrics(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"user_id": user_id}
        if project_id:
            params["project_id"] = project_id
        return self._get("/client/code_intelligence/analytics/ai-agent", params, overrides=overrides)

    def correct_code(
        self,
        code: str,
        language: str,
        project_profile: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "code": code,
            "language": language,
            "project_profile": project_profile or {},
        }
        return self._post("/client/code_intelligence/correct/code", payload, overrides=overrides)

    def correct_config(self, config: str, config_type: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"config": config, "config_type": config_type}
        return self._post("/client/code_intelligence/correct/config", payload)

    def correct_documentation(self, markdown: str, doc_type: str = "README") -> Dict[str, Any]:
        payload: Dict[str, Any] = {"markdown": markdown, "doc_type": doc_type}
        return self._post("/client/code_intelligence/correct/documentation", payload)

    def apply_auto_corrections(
        self,
        user_id: str,
        model_name: str,
        corrections: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "user_id": user_id,
            "model_name": model_name,
            "corrections": corrections,
        }
        return self._post("/client/code_intelligence/auto-correct", payload)

    def get_trust_score(self, user_id: str, model_name: str) -> float:
        params: Dict[str, Any] = {"user_id": user_id, "model_name": model_name}
        data = self._get("/client/code_intelligence/trust-score", params)
        try:
            return float(data.get("trust_score", 0))
        except Exception:
            return 0.0

    def submit_feedback(self, prediction_id: str, accepted: bool) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"prediction_id": prediction_id, "accepted": bool(accepted)}
        return self._post("/client/code_intelligence/feedback", payload)

    def get_auto_correct_stats(self, user_id: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {"user_id": user_id}
        return self._get("/client/code_intelligence/stats", params)

    def get_patterns(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params: Optional[Dict[str, Any]] = {"user_id": user_id} if user_id else None
        data = self._get("/client/code_intelligence/patterns", params)
        if isinstance(data, list):
            return data
        return []

    def predict_correction(
        self,
        input_text: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Predict a code correction before applying it"""
        payload = {
            "input_text": input_text,
            "user_id": user_id,
            "context": context or {}
        }
        return self._post("/client/code_intelligence/predict", payload)

    def correct_tests(
        self,
        test_code: str,
        test_framework: str,
        language: str
    ) -> Dict[str, Any]:
        """Apply test-specific corrections to a test file"""
        payload = {
            "test_code": test_code,
            "test_framework": test_framework,
            "language": language
        }
        return self._post("/client/code_intelligence/correct/tests", payload)
