import requests
import time
import threading
import queue
import uuid
import logging
import os
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger("ai_analytics_client")

class AIAnalytics:
    def __init__(self, api_key: str, environment: str = "prod", collect_content: bool = False):
        if not api_key:
            raise ValueError("API Key is required to initialize AIAnalytics.")
            
        self.api_key = api_key
        # System-defined base URL, override-able via env var for internal dev only
        self.base_url = os.environ.get("TKNOPS_API_URL", "https://api.tknops.io").rstrip("/")
        self.environment = environment
        self.collect_content = collect_content
        self.queue = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def track(
        self,
        model: str,
        provider: str,
        user_id: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        prompt_text: Optional[str] = None,
        response_text: Optional[str] = None,
        feature: Optional[str] = None,
        team: Optional[str] = None,
        agent: Optional[str] = None,
        environment: Optional[str] = None
    ):
        """
        Manual tracking of an AI usage event.
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())
            
        # Only collect content if enabled
        final_prompt = prompt_text if self.collect_content else None
        final_response = response_text if self.collect_content else None
            
        event = {
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "model_name": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "prompt_text": final_prompt,
            "response_text": final_response,
            "feature": feature,
            "team": team,
            "agent": agent,
            "environment": environment or self.environment,
            "tags": tags or [],
            "metadata": metadata or {}
        }
        
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            logger.warning("AIAnalytics queue full. Dropping event.")

    def track_response(
        self,
        response: Any,
        user_id: Optional[str] = None,
        provider: str = "openai",
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        prompt: Optional[str] = None, # Capture the input prompt if available
        feature: Optional[str] = None,
        team: Optional[str] = None,
        agent: Optional[str] = None,
        environment: Optional[str] = None,
        response_type: Optional[str] = None # "openai", "langchain", etc.
    ):
        """
        Automatically track usage from a response object (OpenAI or LangChain).
        """
        if response_type and response_type not in ["openai", "langchain"]:
            raise ValueError(f"Invalid response_type '{response_type}'. Must be one of: ['openai', 'langchain']")

        try:
            data = None
            if response_type == "openai":
                data = self._extract_openai(response)
            elif response_type == "langchain":
                data = self._extract_langchain(response)
            else:
                # Fallback to heuristics
                data = self._extract_metrics(response)

            if not data:
                logger.warning(f"Could not extract metrics from response object (type: {response_type or 'unknown'}).")
                return

            model = data.get('model', 'unknown')
            input_tok = data.get('input_tokens', 0)
            output_tok = data.get('output_tokens', 0)

            # Cost Calculation Logic
            cost = 0.0
            
            # 1. Use manual rates if provided (Client-Side Override)
            if cost_per_1k_input > 0 or cost_per_1k_output > 0:
                cost = (input_tok / 1000 * cost_per_1k_input) + \
                       (output_tok / 1000 * cost_per_1k_output)
            
            # NOTE: Backend will calculate cost if cost_usd is 0.0 based on model registry.

            self.track(
                user_id=user_id,
                model=model,
                provider=provider,
                input_tokens=input_tok,
                output_tokens=output_tok,
                cost_usd=cost,
                tags=tags,
                metadata=metadata,
                session_id=session_id,
                prompt_text=prompt,
                response_text=data.get('response_text'),
                feature=feature,
                team=team,
                agent=agent,
                environment=environment
            )
        except Exception as e:
            logger.error(f"Error tracking response: {e}")

    def _extract_openai(self, response: Any) -> Optional[Dict[str, Any]]:
        if hasattr(response, 'usage') and hasattr(response, 'model'):
            usage = response.usage
            response_text = None
            
            # Try to get text content from choices
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    response_text = choice.message.content
                elif hasattr(choice, 'text'):
                    response_text = choice.text
            
            if hasattr(usage, 'prompt_tokens'):
                return {
                    "model": response.model,
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "response_text": response_text
                }
            elif isinstance(usage, dict):
                 return {
                    "model": response.model,
                    "input_tokens": usage.get('prompt_tokens', 0),
                    "output_tokens": usage.get('completion_tokens', 0),
                    "response_text": response_text
                }
        return None

    def _extract_langchain(self, response: Any) -> Optional[Dict[str, Any]]:
         if hasattr(response, 'response_metadata'):
            meta = response.response_metadata
            response_text = None
            if hasattr(response, 'content'):
                response_text = str(response.content)
                
            if 'token_usage' in meta:
                usage = meta['token_usage']
                return {
                    "model": meta.get('model_name', 'langchain-model'),
                    "input_tokens": usage.get('prompt_tokens', 0),
                    "output_tokens": usage.get('completion_tokens', 0),
                    "response_text": response_text
                }
            if 'openai' in meta and 'usage' in meta:
                 usage = meta['usage']
                 return {
                    "model": meta.get('model_name', 'openai'),
                    "input_tokens": usage.get('prompt_tokens', 0),
                    "output_tokens": usage.get('completion_tokens', 0),
                    "response_text": response_text
                }
         return None

    def _extract_metrics(self, response: Any) -> Optional[Dict[str, Any]]:
        # 1. Try OpenAI-like object (Pydantic or Dict)
        openai_data = self._extract_openai(response)
        if openai_data:
            return openai_data
        
        # 2. Try LangChain
        langchain_data = self._extract_langchain(response)
        if langchain_data:
            return langchain_data

        # 3. Try Raw Config/Dict
        if isinstance(response, dict):
            if 'usage' in response:
                usage = response['usage']
                response_text = None
                if 'choices' in response and len(response['choices']) > 0:
                    c = response['choices'][0]
                    if 'message' in c:
                        response_text = c['message'].get('content')
                    elif 'text' in c:
                        response_text = c.get('text')
                        
                return {
                    "model": response.get('model', 'unknown'),
                    "input_tokens": usage.get('prompt_tokens', 0),
                    "output_tokens": usage.get('completion_tokens', 0),
                    "response_text": response_text
                }

        return None

    def _worker(self):
        while not self._stop_event.is_set():
            try:
                # Batch processing could go here, but simple 1-by-1 for now
                event = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            self._send_event(event)
            self.queue.task_done()

    def _send_event(self, event: Dict[str, Any]):
        url = f"{self.base_url}/track/"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, json=event, headers=headers, timeout=5.0)
            if response.status_code >= 400:
                logger.error(f"Failed to track event: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Exception tracking event: {e}")

    def shutdown(self):
        """Wait for queue to empty and stop worker."""
        self.queue.join()
        self._stop_event.set()
        self._worker_thread.join(timeout=2.0)
