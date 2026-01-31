from __future__ import annotations

from typing import Any, Mapping, Optional
from openai import AsyncOpenAI
from .base_chat_provider import (
    BaseChatProvider, 
    Messages, 
    CompletionResult,
    ProviderError
)


class DeepInfraProvider(BaseChatProvider):
    """
    DeepInfra chat-completions provider via DeepInfra's OpenAI-compatible API.

    DeepInfra OpenAI-compatible base URL:
        https://api.deepinfra.com/v1/openai

    Default Model: Kimi K2 Instruct on DeepInfra:
        "moonshotai/Kimi-K2-Instruct"
    (DeepInfra also offers versioned variants like "moonshotai/Kimi-K2-Instruct-0905".)
    """

    PROVIDER_NAME = "deepinfra"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "moonshotai/Kimi-K2-Instruct",
        base_url: str = "https://api.deepinfra.com/v1/openai",
        default_max_tokens: int = 4000,
        default_temperature: float = 0.0,
        default_top_p: float = 0.95,
        default_frequency_penalty: float = 0.0,
        default_presence_penalty: float = 0.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required for DeepInfraProvider.")
        if not model:
            raise ValueError("model is required for DeepInfraProvider.")
        if not base_url:
            raise ValueError("base_url is required for DeepInfraProvider.")

        self.model = model
        self.base_url = base_url

        self._defaults = {
            "max_tokens": default_max_tokens,
            "temperature": default_temperature,
            "top_p": default_top_p,
            "frequency_penalty": default_frequency_penalty,
            "presence_penalty": default_presence_penalty,
        }

        # DeepInfra exposes an OpenAI-compatible API; the OpenAI SDK works by setting base_url.
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
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

        req: dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "max_tokens": self._defaults["max_tokens"] if max_tokens is None else max_tokens,
            "temperature": self._defaults["temperature"] if temperature is None else temperature,
            "top_p": self._defaults["top_p"] if top_p is None else top_p,
            "frequency_penalty": self._defaults["frequency_penalty"]
            if frequency_penalty is None
            else frequency_penalty,
            "presence_penalty": self._defaults["presence_penalty"]
            if presence_penalty is None
            else presence_penalty,
        }

        # OpenAI SDK (v1+) accepts `timeout` on requests; if your pinned version differs,
        # you can alternatively configure client-level timeouts.
        if timeout is not None:
            req["timeout"] = timeout

        if extras:
            req |= dict(extras)

        try:
            completion = await self._client.chat.completions.create(**req)

            choice0 = completion.choices[0]
            msg = choice0.message
            text = (choice0.message.content or "").strip()

            usage = None
            if getattr(completion, "usage", None) is not None:
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
        Map OpenAI SDK exceptions into ProviderError with retryable hints.
        DeepInfra is OpenAI-compatible, so exception shapes generally mirror the OpenAI SDK.
        """
        cls = e.__class__.__name__

        status_code = getattr(e, "status_code", None)
        if status_code is None:
            status_code = getattr(e, "status", None)

        retryable = False

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

        if isinstance(status_code, int) and status_code in (408, 409, 425, 429, 500, 502, 503, 504):
            retryable = True

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

        msg = str(e) or f"{cls} from DeepInfra provider"
        return ProviderError(
            msg,
            retryable=retryable,
            status_code=status_code if isinstance(status_code, int) else None,
            provider=self.PROVIDER_NAME,
            cause=e,
        )

    async def aclose(self) -> None:
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
