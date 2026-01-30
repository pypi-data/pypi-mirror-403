import os
import logging
import requests
from typing import Optional, Dict, Any
from .exceptions import AuthenticationError, InvalidRequestError, ServerError, LongMemoryError

# Standard library logger
logger = logging.getLogger("longmemory")

# CONSTANTS
PRODUCTION_URL = "https://api.longmemory.io"

class LongMemory:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        user_id: Optional[str] = None, 
        llm_model: Optional[str] = None, 
        llm_api_key: Optional[str] = None,
        verbose: bool = False
    ):
        # 1. Credential Loading
        self.api_key = api_key or os.getenv("LONGMEMORY_API_KEY")
        self.user_id = user_id or os.getenv("LONGMEMORY_USER_ID")
        self.llm_model = llm_model or os.getenv("LLM_MODEL")
        self.llm_api_key = llm_api_key or os.getenv("LLM_API_KEY")
        
        self.verbose = verbose
        
        # 2. Hardcoded Security
        self.base_url = PRODUCTION_URL.rstrip("/")

        if not self.api_key:
            raise AuthenticationError("No API key provided. Set LONGMEMORY_API_KEY env var or pass api_key=...")

        # 3. Connection Setup
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "longmemory-python/0.1.0"
        })

    def _log(self, msg: str):
        if self.verbose:
            print(f"\033[94m[LongMemory]\033[0m {msg}")

    def _request(self, method: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        try:
            # We strictly enforce SSL verification (verify=True)
            response = self.session.request(method, url, json=payload, timeout=30, verify=True)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid LongMemory API Key.")
            elif 400 <= response.status_code < 500:
                raise InvalidRequestError(f"Client Error ({response.status_code}): {response.text}")
            elif response.status_code >= 500:
                raise ServerError(f"Server Error ({response.status_code}): {response.text}")
            
            return response.json()
            
        except requests.exceptions.SSLError:
            raise LongMemoryError("SSL Verification failed. Connection is not secure.")
        except requests.exceptions.RequestException as e:
            raise LongMemoryError(f"Connection failed: {str(e)}") from e

    def add(self, text: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Ingests text into memory."""
        uid = user_id or self.user_id
        if not uid: raise InvalidRequestError("user_id is required.")

        self._log(f"Ingesting memory for user '{uid}'...")
        return self._request("POST", "/v4/ingest", {
            "user_id": uid,
            "text": text,
            "speaker": kwargs.get("speaker", "user"),
            "created_at": kwargs.get("created_at", "")
        })

    def get(self, query: str, user_id: Optional[str] = None, accuracy: str = "standard") -> Dict[str, Any]:
        """
        Retrieves raw context for a query.
        accuracy: 'standard' (faster) or 'high' (more precise/re-ranked).
        """
        uid = user_id or self.user_id
        if not uid: raise InvalidRequestError("user_id is required.")
        
        # Validate accuracy mode
        if accuracy not in ["standard", "high"]:
            raise InvalidRequestError("Accuracy must be either 'standard' or 'high'.")

        self._log(f"Retrieving context ('{accuracy}' mode) for: '{query}'...")
        
        return self._request("POST", "/v4/query", {
            "user_id": uid,
            "query": query,
            "accuracy": accuracy
        })

    def ask(
        self, 
        query: str, 
        user_id: Optional[str] = None, 
        model: Optional[str] = None, 
        api_key: Optional[str] = None,
        accuracy: str = "standard"
    ) -> str:
        """
        Proxies query to LLM.
        accuracy: 'standard' or 'high'.
        """
        uid = user_id or self.user_id
        target_model = model or self.llm_model
        target_key = api_key or self.llm_api_key

        if not uid: raise InvalidRequestError("user_id is required.")
        if not target_model: raise InvalidRequestError("LLM model name is required.")
        if not target_key: raise InvalidRequestError(f"API Key for {target_model} is required.")
        
        if accuracy not in ["standard", "high"]:
            raise InvalidRequestError("Accuracy must be either 'standard' or 'high'.")

        self._log(f"Proxying query to \033[1m{target_model}\033[0m (Accuracy: {accuracy})...")
        
        response = self._request("POST", "/v4/ask", {
            "user_id": uid,
            "query": query,
            "model_provider": target_model,
            "model_api_key": target_key,
            "accuracy": accuracy
        })
        
        self._log("✓ Answer received.")
        return response.get("answer", response)