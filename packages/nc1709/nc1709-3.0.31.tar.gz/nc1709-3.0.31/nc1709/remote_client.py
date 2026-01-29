"""
NC1709 Remote Client
Connects to a remote NC1709 server for LLM access
"""
import os
import json
from typing import Optional, Dict, Any, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class RemoteClient:
    """Client for connecting to remote NC1709 server"""

    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """Initialize remote client

        Args:
            server_url: URL of the NC1709 server (or set NC1709_API_URL env var)
            api_key: API key for authentication (or set NC1709_API_KEY env var)
        """
        self.server_url = (
            server_url or
            os.environ.get("NC1709_API_URL") or
            os.environ.get("NC1709_SERVER_URL") or
            "https://nc1709.lafzusa.com"
        )
        self.api_key = (
            api_key or
            os.environ.get("NC1709_API_KEY")
        )

        if not self.server_url:
            raise ValueError(
                "No server URL provided. This should not happen with default URL."
            )

        # Normalize URL
        self.server_url = self.server_url.rstrip("/")

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Make HTTP request to server

        Args:
            endpoint: API endpoint (e.g., "/api/remote/status")
            method: HTTP method
            data: JSON data for POST requests
            timeout: Request timeout in seconds

        Returns:
            Response JSON
        """
        url = f"{self.server_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "nc1709-client/3.0.11"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = json.dumps(data).encode("utf-8") if data else None

        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                error_json = json.loads(error_body)
                detail = error_json.get("detail", error_body)
            except json.JSONDecodeError:
                detail = error_body

            if e.code == 401:
                raise ConnectionError(
                    f"Authentication failed: {detail}\n"
                    "Set NC1709_API_KEY environment variable with your API key.\n"
                    "Don't have an API key? Request one at: asif90988@gmail.com"
                )
            if e.code == 403:
                raise ConnectionError(
                    f"Not authenticated: {detail}\n\n"
                    "You need an API key to use NC1709.\n\n"
                    "To set up your API key:\n"
                    "  export NC1709_API_KEY=\"your-api-key-here\"\n\n"
                    "Don't have an API key? Request one at: asif90988@gmail.com"
                )
            raise ConnectionError(f"Server error ({e.code}): {detail}")
        except URLError as e:
            raise ConnectionError(
                f"Cannot connect to NC1709 server at {self.server_url}\n"
                f"Error: {e.reason}\n"
                "Make sure the server is running and accessible."
            )

    def check_status(self) -> Dict[str, Any]:
        """Check server status

        Returns:
            Server status information
        """
        return self._make_request("/api/remote/status")

    def complete(
        self,
        prompt: str,
        task_type: str = "general",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get LLM completion from remote server

        Args:
            prompt: User prompt
            task_type: Task type (reasoning, coding, tools, general, fast)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLM response text
        """
        data = {
            "prompt": prompt,
            "task_type": task_type,
            "temperature": temperature
        }

        if system_prompt:
            data["system_prompt"] = system_prompt
        if max_tokens:
            data["max_tokens"] = max_tokens

        result = self._make_request("/api/remote/complete", method="POST", data=data)
        return result.get("response", "")

    def chat_simple(self, message: str) -> str:
        """Send chat message to remote server (uses full reasoning engine)

        Args:
            message: User message

        Returns:
            Assistant response
        """
        data = {"message": message}
        result = self._make_request("/api/remote/chat", method="POST", data=data)
        return result.get("response", "")

    def agent_chat(
        self,
        messages: list,
        cwd: str,
        tools: list = None
    ) -> Dict[str, Any]:
        """Send agent chat request - returns LLM response for local tool execution

        This is the new architecture where:
        - Server only runs LLM (thinking)
        - Client executes tools locally

        Args:
            messages: Conversation history [{"role": "user/assistant", "content": "..."}]
            cwd: Client's current working directory
            tools: List of available tools on client

        Returns:
            Dict with 'response' (LLM output that may contain tool calls)
        """
        data = {
            "messages": messages,
            "cwd": cwd,
            "tools": tools or [],
            "model": "qwen2.5-coder:7b-instruct"
        }
        return self._make_request("/api/remote/agent", method="POST", data=data)

    def is_connected(self) -> bool:
        """Check if connected to server

        Returns:
            True if server is reachable
        """
        try:
            status = self.check_status()
            return status.get("status") == "ok"
        except Exception:
            return False

    def index_code(
        self,
        user_id: str,
        files: list,
        project_name: str = None
    ) -> Dict[str, Any]:
        """Index code files on the server's vector database

        Args:
            user_id: Unique user/session identifier
            files: List of {"path": "...", "content": "...", "language": "..."}
            project_name: Optional project name for grouping

        Returns:
            Indexing result with stats
        """
        data = {
            "user_id": user_id,
            "files": files,
            "project_name": project_name
        }
        return self._make_request("/api/remote/index", method="POST", data=data)

    def search_code(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        project_name: str = None
    ) -> Dict[str, Any]:
        """Search indexed code on the server

        Args:
            user_id: User identifier
            query: Search query
            n_results: Number of results to return
            project_name: Optional project filter

        Returns:
            Search results
        """
        data = {
            "user_id": user_id,
            "query": query,
            "n_results": n_results,
            "project_name": project_name
        }
        return self._make_request("/api/remote/search", method="POST", data=data)



    def agent_chat_streaming(
        self,
        messages: list,
        cwd: str,
        tools: list = None,
        on_status: callable = None
    ) -> Dict[str, Any]:
        """Send agent chat request with streaming to prevent timeout

        Uses Server-Sent Events to keep connection alive during long requests.

        Args:
            messages: Conversation history
            cwd: Client current working directory
            tools: List of available tools
            on_status: Optional callback for status updates

        Returns:
            Dict with response (LLM output that may contain tool calls)
        """
        url = f"{self.server_url}/api/remote/agent/stream"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "nc1709-client/3.0.27",
            "Accept": "text/event-stream"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = {
            "messages": messages,
            "cwd": cwd,
            "tools": tools or [],
            "model": "qwen2.5-coder:7b-instruct"
        }

        body = json.dumps(data).encode("utf-8")
        req = Request(url, data=body, headers=headers, method="POST")

        try:
            with urlopen(req, timeout=600) as response:
                result = None
                for line in response:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        event_data = json.loads(line[6:])
                        status = event_data.get("status")

                        if on_status and status in ("processing", "generating"):
                            on_status(event_data.get("message", status))

                        if status == "complete":
                            result = event_data
                        elif status == "error":
                            raise ConnectionError(f"Server error: {event_data.get('message')}")

                if result:
                    return {
                        "response": result.get("response", ""),
                        "model": result.get("model"),
                        "usage": result.get("usage", {})
                    }
                else:
                    raise ConnectionError("No response received from streaming endpoint")

        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise ConnectionError(f"Server error ({e.code}): {error_body}")
        except URLError as e:
            raise ConnectionError(f"Cannot connect to server: {e.reason}")

class RemoteLLMAdapter:
    """
    LLM Adapter that uses RemoteClient for server-side inference.
    
    This adapter provides the same interface as the local LLMAdapter,
    allowing the Agent to work transparently with remote LLM.
    
    Architecture:
    - Server handles LLM inference (thinking)
    - Client handles tool execution (acting)
    """

    def __init__(self, remote_client: RemoteClient):
        """Initialize the remote LLM adapter

        Args:
            remote_client: Configured RemoteClient instance
        """
        self.client = remote_client
        self.conversation_history: List[Dict[str, str]] = []
        self._model_name = "qwen2.5-coder:7b-instruct"

    @property
    def model_name(self) -> str:
        """Get the model name"""
        return self._model_name

    def chat(
        self,
        messages: List[Dict[str, str]],
        task_type: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Chat with the remote LLM using a message list (for agent use)

        This method is designed for the Agent class which manages its own
        conversation history and passes complete message lists.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            task_type: Type of task (ignored - server handles routing)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response text
        """
        import os
        
        # Use agent_chat endpoint for full message history support
        result = self.client.agent_chat(
            messages=messages,
            cwd=os.getcwd(),
            tools=[]  # Tools are registered client-side
        )
        
        response = result.get("response", "")
        
        # Handle different response formats
        if isinstance(response, dict):
            # If response is a dict, extract content
            response = response.get("content", str(response))
        
        return response

    def complete(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        model: Optional[str] = None
    ) -> str:
        """Get completion from remote LLM

        Args:
            prompt: User's prompt
            task_type: Type of task
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream (not supported in remote mode)
            model: Model override (ignored - server decides)

        Returns:
            LLM response text
        """
        if stream:
            # Streaming not supported in remote mode, fall back to regular
            pass
            
        return self.client.complete(
            prompt=prompt,
            task_type=task_type or "tools",
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []

    def get_model_info(self, task_type: str = None) -> str:
        """Get model info string

        Args:
            task_type: Task type (ignored)

        Returns:
            Model info string
        """
        return f"remote:{self._model_name}"

    def is_available(self) -> bool:
        """Check if remote LLM is available

        Returns:
            True if server is reachable
        """
        return self.client.is_connected()


def get_remote_client() -> Optional[RemoteClient]:
    """Get remote client if configured

    Returns:
        RemoteClient instance if NC1709_API_URL is set, None otherwise
    """
    try:
        return RemoteClient()
    except ValueError:
        return None


def get_remote_llm_adapter(remote_client: Optional[RemoteClient] = None) -> Optional[RemoteLLMAdapter]:
    """Get a RemoteLLMAdapter instance

    Args:
        remote_client: Optional pre-configured RemoteClient

    Returns:
        RemoteLLMAdapter instance or None if not configured
    """
    client = remote_client or get_remote_client()
    if client:
        return RemoteLLMAdapter(client)
    return None




def is_remote_mode() -> bool:
    """Check if running in remote mode

    Returns:
        True - always in remote mode with default server
    """
    return True
