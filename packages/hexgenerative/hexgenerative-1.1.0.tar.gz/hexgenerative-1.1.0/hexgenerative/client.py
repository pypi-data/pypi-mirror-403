"""
Hexa Generative AI - Python Client
"""

import httpx
from typing import List, Optional, Dict, Any, Union
from .models import ChatMessage, ChatCompletion


class HexaAIError(Exception):
    """Base exception for Hexa AI errors"""
    def __init__(self, message: str, status_code: int = None, error_type: str = None):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(self.message)


class HexaAI:
    """
    Hexa AI Python Client
    
    Usage:
        from hexgenerative import HexaAI
        
        client = HexaAI(api_key="hgx-...")
        
        response = client.chat.completions.create(
            model="hexa-pro",
            messages=[
                {"role": "user", "content": "Hello!"}
            ]
        )
        
        print(response.choices[0].message.content)
    """
    
    DEFAULT_BASE_URL = "https://api.shipflowstore.store"
    
    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self.chat = Chat(self)
        self.agent = Agent(self)
        self.rag = RAG(self)
        self.context = Context(self)
        self.code = Code(self)
        self.tools = Tools(self)
        self.disaster = DisasterAlert(self)
        self.audio = Audio(self)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "hexgenerative-python/1.0.0"
        }
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error = error_data.get("error", {})
                raise HexaAIError(
                    message=error.get("message", "Request failed"),
                    status_code=response.status_code,
                    error_type=error.get("type", "api_error")
                )
            
            return response.json()
    
    async def _async_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error = error_data.get("error", {})
                raise HexaAIError(
                    message=error.get("message", "Request failed"),
                    status_code=response.status_code,
                    error_type=error.get("type", "api_error")
                )
            
            return response.json()


class Chat:
    def __init__(self, client: HexaAI):
        self._client = client
        self.completions = Completions(client)


class Completions:
    def __init__(self, client: HexaAI):
        self._client = client
    
    def create(
        self,
        messages: List[Union[Dict[str, str], ChatMessage]],
        model: str = "hexa-balanced",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        task: Optional[str] = None,
        optimize_for: Optional[str] = None,
        auto_select: bool = False,
        **kwargs
    ) -> ChatCompletion:
        """
        Create a chat completion.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use (hexa-instant, hexa-balanced, hexa-pro, etc.)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            task: Task type for auto-routing (fast_response, reasoning, coding)
            optimize_for: Optimization preference (speed, quality, cost)
            auto_select: Let Hexa AI pick the best model
        
        Returns:
            ChatCompletion object
        """
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append(msg.to_dict())
            else:
                formatted_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if task:
            payload["task"] = task
        if optimize_for:
            payload["optimize_for"] = optimize_for
        if auto_select:
            payload["auto_select"] = auto_select
        
        payload.update(kwargs)
        
        response = self._client._request("POST", "/v1/chat/completions", payload)
        return ChatCompletion.from_dict(response)
    
    async def acreate(
        self,
        messages: List[Union[Dict[str, str], ChatMessage]],
        model: str = "hexa-balanced",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        task: Optional[str] = None,
        optimize_for: Optional[str] = None,
        auto_select: bool = False,
        **kwargs
    ) -> ChatCompletion:
        """
        Async version of create().
        """
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append(msg.to_dict())
            else:
                formatted_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if task:
            payload["task"] = task
        if optimize_for:
            payload["optimize_for"] = optimize_for
        if auto_select:
            payload["auto_select"] = auto_select
        
        payload.update(kwargs)
        
        response = await self._client._async_request("POST", "/v1/chat/completions", payload)
        return ChatCompletion.from_dict(response)


class Agent:
    def __init__(self, client: HexaAI):
        self._client = client
    
    def run(self, task: str, model: str = "hexa-ultra", servers: List[str] = None) -> Dict[str, Any]:
        """Run an agentic task."""
        payload = {"task": task, "model": model}
        if servers:
            payload["servers"] = servers
        return self._client._request("POST", "/v1/agent/run", payload)

class RAG:
    def __init__(self, client: HexaAI):
        self._client = client
    
    def upload(self, title: str, content: str) -> Dict[str, Any]:
        """Upload a document to knowledge base."""
        return self._client._request("POST", "/v1/rag/upload", {"title": title, "content": content})
    
    def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Search knowledge base."""
        return self._client._request("POST", "/v1/rag/search", {"query": query, "top_k": top_k})

class Context:
    def __init__(self, client: HexaAI):
        self._client = client
        
    def create(self, system_prompt: str = "You are a helpful assistant.") -> Dict[str, Any]:
        """Create a new 300K token context session."""
        return self._client._request("POST", "/v1/context/create", {"system_prompt": system_prompt})
        
    def add(self, session_id: str, message: Dict[str, str]) -> Dict[str, Any]:
        """Add a message to context session."""
        return self._client._request("POST", "/v1/context/add", {"session_id": session_id, "message": message})

class Code:
    def __init__(self, client: HexaAI):
        self._client = client
        
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code in sandbox."""
        return self._client._request("POST", "/v1/code/execute", {"code": code})

class Tools:
    def __init__(self, client: HexaAI):
        self._client = client
        
    def list(self) -> Dict[str, Any]:
        """List available tools."""
        return self._client._request("GET", "/v1/tools")


class DisasterAlert:
    def __init__(self, client: HexaAI):
        self._client = client
        
    def check_emergency(self, lat: float, lon: float, radius: float = 111) -> Dict[str, Any]:
        """
        Check for emergencies in area (earthquake, tornado, etc).
        Returns siren instructions for frontend.
        """
        return self._client._request("POST", "/v1/emergency/check", {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius
        })


class Audio:
    def __init__(self, client: HexaAI):
        self._client = client
        self.speech = Speech(client)


class Speech:
    def __init__(self, client: HexaAI):
        self._client = client

    def create(
        self,
        input: str,
        voice: str = "tara",
        speed: float = 1.0,
        stream: bool = False
    ) -> Union[bytes, Any]:
        """
        Generate speech from text.
        
        Args:
            input: Text to generate speech from
            voice: Voice ID (tara, leah, jess, etc.)
            speed: Speed multiplier (0.5 - 2.0)
            stream: If True, returns a generator/iterator of bytes (not fully supported in sync wrapper yet)
        
        Returns:
            WAV audio bytes
        """
        payload = {
            "input": input,
            "voice": voice,
            "speed": speed,
            "stream": stream
        }
        
        # We need to handle raw bytes response, not JSON
        # The _request helper expects JSON response. We need a raw request helper or modification.
        # For now, let's use a custom request implementation here for simplicity using existing _get_headers
        url = f"{self._client.base_url}/v1/audio/speech"
        
        with httpx.Client(timeout=self._client.timeout) as client:
            # Note: For strict 'stream=True', we should use client.stream, but this is a sync wrapper.
            # Simulating stream or just returning bytes for now.
            response = client.post(
                url,
                headers=self._client._get_headers(),
                json=payload
            )
            
            if response.status_code != 200:
                raise HexaAIError(f"TTS failed: {response.text}", response.status_code)
                
            return response.content

    async def acreate(
        self,
        input: str,
        voice: str = "tara",
        speed: float = 1.0,
        stream: bool = False
    ) -> Union[bytes, Any]:
        """Async version of create."""
        payload = {
            "input": input,
            "voice": voice,
            "speed": speed,
            "stream": stream
        }
        
        url = f"{self._client.base_url}/v1/audio/speech"
        
        async with httpx.AsyncClient(timeout=self._client.timeout) as client:
            if stream:
                # For streaming, we return the response object itself (context manager needs handling by user)
                # or an async generator.
                # Simplest for SDK: return the bytes if not truly streaming-ready api wrapper.
                # Or implementing async generator:
                pass
            
            response = await client.post(
                url,
                headers=self._client._get_headers(),
                json=payload
            )
             
            if response.status_code != 200:
                raise HexaAIError(f"TTS failed: {response.text}", response.status_code)
            
            return response.content

