import abc

from dataclasses import dataclass
from typing import Any, List, Dict, Mapping, Optional, Iterable, TypedDict, Literal


# -----------------------------
# Canonical message format
# -----------------------------

Role = Literal["system", "user", "assistant", "tool"]

class ToolCallFunction(TypedDict):
    name: str
    arguments: str  # JSON string

class ToolCall(TypedDict):
    id: str
    type: Literal["function"]
    function: ToolCallFunction

class ChatMessage(TypedDict, total=False):
    role: Role
    content: str

    # assistant-only (when requesting tools)
    tool_calls: List[ToolCall]

    # tool-only (tool result message)
    tool_call_id: str


Messages = Iterable[ChatMessage]


# -----------------------------
# Provider result + errors
# -----------------------------

@dataclass(frozen=True)
class CompletionResult:
    text: str
    raw: Any = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[ToolCall]] = None


class ProviderError(Exception):
    """
    Generic provider exception.

    Attributes:
        retryable: Whether retrying the request might succeed (timeouts, rate limits, transient 5xx, etc.).
        status_code: HTTP-ish status code if known.
        provider: Name of provider implementation (e.g. "azure_openai").
    """
    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        status_code: Optional[int] = None,
        provider: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)

        self.retryable = retryable
        self.status_code = status_code
        self.provider = provider
        self.__cause__ = cause


class BaseChatProvider(abc.ABC):
    """
    Minimal interface your core/session layer can depend on.
    Providers should accept OpenAI-style chat messages and return assistant text.
    """

    @abc.abstractmethod
    async def complete(
        self,
        messages: Messages,
        *,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> CompletionResult:
        """
        Generate a completion for the given messages.
        `extra` can be used for provider-specific fields without changing the interface.
        """
        raise NotImplementedError

    async def aclose(self) -> None:
        """Optional: close underlying HTTP clients/resources."""
        return
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()
