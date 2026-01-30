"""
Proxy service client mixin
"""

from typing import Any, Dict, List, Optional


class ProxyClientMixin:
    """Proxy service client mixin for LLM interactions"""

    def chat_proxy(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the proxy
        
        Args:
            model: Model name to use
            messages: List of message objects with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response (currently only sync supported in SDK)
            
        Returns:
            LLM response with memory-injected context
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        return self._post("/client/proxy/chat", json=payload)
