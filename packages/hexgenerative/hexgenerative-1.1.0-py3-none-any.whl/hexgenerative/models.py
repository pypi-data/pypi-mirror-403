from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ChatMessage:
    role: str
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class Choice:
    index: int
    message: ChatMessage
    finish_reason: Optional[str]


@dataclass
class HexaMetadata:
    processing_time_ms: float
    tokens_per_second: float
    cost_usd: float
    infrastructure: str


@dataclass
class ChatCompletion:
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    provider: str
    hexa_metadata: Optional[HexaMetadata]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatCompletion":
        choices = []
        for c in data.get("choices", []):
            msg = ChatMessage(
                role=c["message"]["role"],
                content=c["message"]["content"]
            )
            choices.append(Choice(
                index=c["index"],
                message=msg,
                finish_reason=c.get("finish_reason")
            ))
        
        usage_data = data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        )
        
        meta_data = data.get("hexa_metadata")
        hexa_metadata = None
        if meta_data:
            hexa_metadata = HexaMetadata(
                processing_time_ms=meta_data.get("processing_time_ms", 0),
                tokens_per_second=meta_data.get("tokens_per_second", 0),
                cost_usd=meta_data.get("cost_usd", 0),
                infrastructure=meta_data.get("infrastructure", "")
            )
        
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
            provider=data.get("provider", "Hexa AI"),
            hexa_metadata=hexa_metadata
        )
@dataclass
class ToolFunction:
    name: str
    description: str
    parameters: Dict[str, Any]

@dataclass
class Tool:
    type: str # "function"
    function: ToolFunction

@dataclass
class AgentTask:
    task_id: str
    status: str
    result: Optional[str]
    current_step: int
    thoughts: List[str]
    created_at: str
    completed_at: Optional[str]

@dataclass
class RAGDocument:
    id: str
    title: str
    chunks: int
    created_at: str

@dataclass
class RAGSearchResult:
    doc_id: str
    chunk_text: str
    score: float
    bm25_score: float
    semantic_score: float

@dataclass
class ContextSession:
    session_id: str
    total_tokens: int
    max_tokens: int
    messages: int 
