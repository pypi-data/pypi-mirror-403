from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class LLMRole(str, Enum):
    """Message role in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Single message in conversation."""
    role: LLMRole
    content: str


@dataclass
class LLMRequest:
    """Request to LLM provider."""
    messages: List[LLMMessage]
    model: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    stop: Optional[List[str]] = None
    stream: bool = False


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str  # "stop", "length", "content_filter"


@dataclass
class LLMStreamChunk:
    """Streaming response chunk."""
    content: str
    is_final: bool = False
    finish_reason: Optional[str] = None
