from __future__ import annotations

from typing import Any, Mapping, Optional
from openai import AsyncAzureOpenAI
from .base_chat_provider import (
    BaseChatProvider, 
    Messages, 
    CompletionResult,
    ProviderError
)


class AzureOpenAIProvider(BaseChatProvider):
    """
    Azure OpenAI chat-completions provider using the OpenAI Python SDK (AsyncAzureOpenAI).

    Notes:
      - In Azure, `model` is typically your *deployment name*.
      - This provider assumes OpenAI-style message format: [{"role": "...", "content": "..."}]
    """

    PROVIDER_NAME = "azure_openai"

    def __init__(
        self,
        *,
        azure_endpoint: str,
        api_key: str,
        api_version: str,
        model: str,
        default_max_tokens: int = 4000,
        default_temperature: float = 0.0,
        default_top_p: float = 0.95,
        default_frequency_penalty: float = 0.0,
        default_presence_penalty: float = 0.0,
    ) -> None:
        if not azure_endpoint or not api_key or not api_version or not model:
            raise ValueError("azure_endpoint, api_key, api_version, and model are required.")

        self.model = model

        self._defaults = {
            "max_tokens": default_max_tokens,
            "temperature": default_temperature,
            "top_p": default_top_p,
            "frequency_penalty": default_frequency_penalty,
            "presence_penalty": default_presence_penalty,
        }

        self._client = AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
        )

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
        extras: Optional[Mapping[str, Any]] = None,
    ) -> CompletionResult:
        if not messages:
            raise ProviderError(
                "messages cannot be empty",
                retryable=False,
                provider=self.PROVIDER_NAME,
            )

        # Merge defaults with per-call overrides
        req = {
            "model": self.model,
            "messages": list(messages),
            "max_tokens": self._defaults["max_tokens"] if max_tokens is None else max_tokens,
            "temperature": self._defaults["temperature"] if temperature is None else temperature,
            "top_p": self._defaults["top_p"] if top_p is None else top_p,
            "frequency_penalty": self._defaults["frequency_penalty"] if frequency_penalty is None else frequency_penalty,
            "presence_penalty": self._defaults["presence_penalty"] if presence_penalty is None else presence_penalty,
        }

        if timeout is not None:
            req["timeout"] = timeout

        if extras:
            req |= dict(extras)

        try:
            completion = await self._client.chat.completions.create(**req)

            # OpenAI SDK shape: choices[0].message.content
            choice0 = completion.choices[0]
            msg = choice0.message
            text = (choice0.message.content or "").strip()

            usage = None
            # usage field varies across SDK versions; try best-effort
            if getattr(completion, "usage", None) is not None:
                # could be pydantic-like object; convert carefully
                try:
                    usage = dict(completion.usage)  # type: ignore[arg-type]
                except Exception:
                    try:
                        usage = completion.usage.model_dump()  # type: ignore[attr-defined]
                    except Exception:
                        usage = None

            tool_calls_out = None
            tc_list = getattr(msg, "tool_calls", None)
            if tc_list:
                tool_calls_out = []
                for tc in tc_list:
                    fn = getattr(tc, "function", None)
                    tool_calls_out.append({
                        "id": getattr(tc, "id", ""),
                        "type": getattr(tc, "type", "function"),
                        "function": {
                            "name": getattr(fn, "name", "") if fn else "",
                            "arguments": getattr(fn, "arguments", "{}") if fn else "{}",
                        },
                    })

            return CompletionResult(
                text=text,
                raw=completion,
                model=getattr(completion, "model", None),
                finish_reason=getattr(choice0, "finish_reason", None),
                usage=usage,
                tool_calls=tool_calls_out,
            )

        except Exception as e:
            raise self._to_provider_error(e) from e

    def _to_provider_error(self, e: Exception) -> ProviderError:
        """
        Map OpenAI SDK exceptions (which vary by SDK version) into ProviderError with retryable hints.
        This is intentionally defensive: it uses class-name heuristics and any available status code.
        """
        cls = e.__class__.__name__

        # Try to extract a status code if present
        status_code = getattr(e, "status_code", None)
        if status_code is None:
            status_code = getattr(e, "status", None)

        # Heuristic retryability
        retryable = False

        # Common transient categories across SDK versions
        transient_names = {
            "APITimeoutError",
            "Timeout",
            "TimeoutError",
            "APIConnectionError",
            "ConnectionError",
            "RateLimitError",
            "InternalServerError",
            "ServiceUnavailableError",
        }
        if cls in transient_names:
            retryable = True

        # If we got a status code, use it
        if isinstance(status_code, int):
            if status_code in (408, 409, 425, 429, 500, 502, 503, 504):
                retryable = True

        # Non-retryable (auth/permission/bad request) hints
        non_retryable_names = {
            "AuthenticationError",
            "PermissionDeniedError",
            "BadRequestError",
            "InvalidRequestError",
            "NotFoundError",
            "UnprocessableEntityError",
        }
        if cls in non_retryable_names:
            retryable = False

        msg = str(e) or f"{cls} from Azure OpenAI provider"
        return ProviderError(
            msg,
            retryable=retryable,
            status_code=status_code if isinstance(status_code, int) else None,
            provider=self.PROVIDER_NAME,
            cause=e,
        )

    async def aclose(self) -> None:
        # Different SDK versions expose different close methods; best-effort.
        client = self._client
        for method_name in ("aclose", "close"):
            m = getattr(client, method_name, None)
            if callable(m):
                try:
                    res = m()
                    if hasattr(res, "__await__"):
                        await res  # type: ignore[misc]
                except Exception:
                    pass
                break