import json
import logging
import time
import tempfile
import os
import asyncio
import aiohttp
import openai
import inspect
import re

from typing import Any, Callable, Awaitable, Optional, Dict, Mapping, Union, List

from ..utility_base import UtilityBase
from ..logger import Logger, LogWrapper
from .providers import BaseChatProvider, ProviderError


ToolCallable = Union[
    Callable[..., Any],
    Callable[..., Awaitable[Any]],
]


# Define exceptions
class ChatClientError(Exception):
    """Custom exception for OpenAIChatClient errors."""
    pass


class OpenAIChatClient(UtilityBase):
    """
    A wrapper for interacting with Azure OpenAI.
    """
    SESSION_DIR = ".sessions"

    def __init__(
            self,
            provider: BaseChatProvider,
            *,
            default_system_message: str = "You are a helpful assistant.",
            max_tokens: int = 4000,
            temperature: float = 0.0,
            top_p: float = 0.95,
            frequency_penalty: float = 0.0,
            presence_penalty: float = 0.0,
            include_message_history: bool = True,
            save_sessions_to_disk: bool = True,
            verbose: bool = False,
            log_messages: bool = False,
            logger: logging.Logger | Logger | LogWrapper | None = None,
            log_level: Optional[int] = None,
            store_tool_messages: bool = False,
            strip_thinking: bool = False,
            thinking_tag_patterns: Optional[list[str]] = None
        ):
        """
        Initializes the Chat client with the provided parameters.

        Args:
            provider (BaseChatProvider): Chat client provider.
            default_system_message (str, optional): Default system message to guide the LLM's behavior. Defaults to "You are a helpful assistant.".
            max_tokens (int, optional): Maximum tokens for the response. Defaults to 4000.
            temperature (float, optional): Sampling temperature for randomness. Defaults to 0.0.
            top_p (float, optional): Probability for nucleus sampling. Defaults to 0.95.
            frequency_penalty (float, optional): Penalize repeated tokens. Defaults to 0.0.
            presence_penalty (float, optional): Penalize repeated topics. Defaults to 0.0.
            include_message_history (bool, optional): Whether to include full history in requests. Defaults to True.
            save_sessions_to_disk (bool, optional): Whether to backup the chat history onto the hard drive. Defaults to True.
            verbose (bool, optional): If true debug messages are logged during the operations.
            log_messages (bool, optional): If true messages and system messages are logged too.
            logger (Optional[Union[logging.Logger, Logger, LogWrapper]], optional): Optional logger instance. If not provided, a default logger is used.
            log_level (Optional[int], optional): Optional log level. If not provided, INFO level will be used for logging.
            store_tool_messages (bool, optional): If true, tool-call messages and tool results are stored in session history too.
            strip_thinking (bool, optional): If true, strips thinking tags from model responses.
            thinking_tag_patterns (Optional[list[str]], optional): Custom regex patterns for thinking tags to strip.
        """
        # Init base class
        super().__init__(verbose, logger, log_level)
        self.log_messages = log_messages

        # Model configuration
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

        # Client configuration
        self.max_tool_rounds = 8
        self.tools: Dict[str, ToolCallable] = {}
        self.tool_schemas: List[dict] = []
        self.include_message_history = include_message_history
        self.default_system_message = {"role": "system", "content": default_system_message}
        self.store_tool_messages = store_tool_messages

        self.strip_thinking = strip_thinking
        self.thinking_tag_patterns = thinking_tag_patterns or [
            r"<think>.*?</think>",          # common
            r"<thinking>.*?</thinking>",    # some models
        ]
        self._thinking_re = re.compile("|".join(self.thinking_tag_patterns), re.DOTALL | re.IGNORECASE)

        # Provider Client
        self.async_client = provider

        # Session locks (guards session mutation + disk writes)
        self._session_locks: Dict[str, asyncio.Lock] = {}

        # Initialize storage
        self.save_sessions_to_disk = save_sessions_to_disk
        if save_sessions_to_disk:
            os.makedirs(self.SESSION_DIR, exist_ok=True)
            self._load_all_sessions_from_disk()
        else:
            self.sessions = {}

        # Ensure locks exist for loaded sessions
        for sid in self.sessions.keys():
            self._session_locks.setdefault(sid, asyncio.Lock())

        self._log(f"ChatClient initialized successfully. Conversation history {'enabled' if include_message_history else 'disabled'}.")

    def register_tool(
        self,
        *,
        schema: Mapping[str, Any],
        func: ToolCallable,
        name: Optional[str] = None,
        max_tool_rounds: Optional[int] = None,
        overwrite: bool = True,
        insert_front: bool = False,
    ) -> str:
        """
        Register a single tool:
          - stores the OpenAI-compatible schema (for request payload)
          - stores the callable (sync or async)
          - optionally updates max tool-calling rounds

        Args:
            schema: OpenAI-compatible tool schema dict:
                {
                  "type": "function",
                  "function": {
                    "name": "...",
                    "description": "...",
                    "parameters": {...json schema...}
                  }
                }
            func: Callable to execute (sync or async). It should accept **kwargs matching parameters.
            name: Optional explicit name override. If None, extracted from schema["function"]["name"].
            max_tool_rounds: Optional new cap for tool-call loops.
            overwrite: If False, refuses to overwrite an existing tool with same name.
            insert_front: If True, inserts schema at the front of tool_schemas (priority).

        Returns:
            The registered tool name.
        """
        if not isinstance(schema, Mapping):
            raise ValueError("schema must be a mapping/dict.")
        if not callable(func):
            raise ValueError("func must be callable.")

        # Validate schema shape
        schema_type = schema.get("type")
        fn_block = schema.get("function")
        if schema_type != "function" or not isinstance(fn_block, Mapping):
            raise ValueError("schema must be OpenAI-compatible with type='function' and a 'function' object.")

        schema_name = fn_block.get("name")
        tool_name = (name or schema_name)
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("Tool name must be a non-empty string (either pass name= or set schema['function']['name']).")

        # Update tool rounds cap if requested
        if max_tool_rounds is not None:
            if not isinstance(max_tool_rounds, int) or max_tool_rounds <= 0:
                raise ValueError("max_tool_rounds must be a positive integer.")
            self.max_tool_rounds = max_tool_rounds

        # Register callable
        if (not overwrite) and (tool_name in self.tools):
            raise ValueError(f"Tool '{tool_name}' is already registered (overwrite=False).")
        self.tools[tool_name] = func

        # Ensure schema name matches tool_name
        schema_copy = dict(schema)
        fn_copy = dict(fn_block)
        fn_copy["name"] = tool_name
        schema_copy["function"] = fn_copy

        # Upsert schema: replace existing schema with same function.name, else add
        replaced = False
        for i, existing in enumerate(self.tool_schemas):
            try:
                ex_fn = existing.get("function", {})
                ex_name = ex_fn.get("name")
            except Exception:
                ex_name = None

            if ex_name == tool_name:
                self.tool_schemas[i] = schema_copy
                replaced = True
                break

        if not replaced:
            if insert_front:
                self.tool_schemas.insert(0, schema_copy)
            else:
                self.tool_schemas.append(schema_copy)

        return tool_name

    def request_completion(
            self,
            message_content: str,
            session_id: Optional[str] = None,
            timeout: int = 30,
            retries: int = 3,
            retry_delay: float = 2.0
        ) -> str:
        """
        Sends a new message to the LLM and retrieves the response with retry support.
        Do not use this function inside a running event loop.

        Args:
            message_content (str): The user's message to send to the LLM.
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.
            timeout (int, optional): Timeout for the API request (in seconds). Defaults to 30.
            retries (int, optional): Number of retry attempts for transient failures. Defaults to 3.
            retry_delay (float, optional): Delay (in seconds) between retries. Defaults to 2.0.

        Returns:
            str: The LLM's response.

        Raises:
            ValueError: If message content is empty.
            ChatClientError: If the request fails after all retries.
        """
        if not message_content.strip():
            raise ValueError("Message content cannot be empty.")

        try:
            asyncio.get_running_loop()
            raise ChatClientError("request_completion() cannot be used inside a running event loop; use request_completion_async().")
        except RuntimeError:
            pass

        # Request a completion, try it again "retries" times, if it fails
        for attempt in range(retries):
            try:
                response = asyncio.run(self._request_completion(message_content, session_id, timeout))
                return response
            except Exception as e:
                self._log_exception(e)
                self._log_warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay * (2 ** attempt):.2f} seconds...")
                time.sleep(retry_delay * (2 ** attempt))

                if (attempt + 1) == retries:
                    raise ChatClientError("Failed to complete the request after multiple retries.") from e

    async def request_completion_async(
            self,
            message_content: str,
            session_id: Optional[str] = None,
            timeout: int = 30,
            retries: int = 3,
            retry_delay: float = 2.0
        ) -> str:
        """
        Sends a new message to the LLM and retrieves the response with retry support asynchronously.

        Args:
            message_content (str): The user's message to send to the LLM.
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.
            timeout (int, optional): Timeout for the API request (in seconds). Defaults to 30.
            retries (int, optional): Number of retry attempts for transient failures. Defaults to 3.
            retry_delay (float, optional): Delay (in seconds) between retries. Defaults to 2.0.

        Returns:
            str: The LLM's response.

        Raises:
            ValueError: If message content is empty.
            ChatClientError: If the request fails after all retries.
        """
        if not message_content.strip():
            raise ValueError("Message content cannot be empty.")

        for attempt in range(retries):
            try:
                response = await self._request_completion(message_content, session_id, timeout)
                return response
            except Exception as e:
                self._log_warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay * (2 ** attempt):.2f} seconds...")
                await asyncio.sleep(retry_delay * (2 ** attempt))

                if (attempt + 1) == retries:
                    raise ChatClientError("Failed to complete the request after multiple retries.") from e

    def trim_conversation_history(self, session_id: Optional[str] = None, max_length: int = 50) -> None:
        """
        Trims the conversation history to the last `max_length` messages.

        Args:
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.
            max_length (int, optional): The maximum number of messages to retain in the history. Defaults to 50.

        Raises:
            ValueError: If max_length is not positive.
        """
        if max_length <= 0:
            raise ValueError("`max_length` must be a positive integer.")

        session_id = self._validate_session(session_id)
        sys_msg = self.sessions[session_id][:1]
        rest = self.sessions[session_id][1:]
        self._log(f"Trimming conversation history for session `{session_id}`")

        # Keep only conversational messages (user + final assistant), drop tool + assistant(tool_calls)
        convo = [
            m for m in rest
            if m.get("role") in ("user", "assistant") and "tool_calls" not in m
        ]

        self.sessions[session_id] = sys_msg + convo[-max_length:]
        self._save_session_to_disk(session_id)

    def get_message_count(self, session_id: Optional[str] = None) -> int:
        """
        Gets the message count from the message history between the user and the LLM.

        Args:
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.

        Returns:
            int: The number of messages in the session.
        """
        session_id = self._validate_session(session_id)

        return len(self.sessions[session_id])

    def change_system_message(self, system_message: str, session_id: Optional[str] = None) -> None:
        """
        Changes the default system message.

        Args:
            system_message (str): The new system message for the completion API.
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.

        Raises:
            ValueError: If system_message is empty.
        """
        if not system_message.strip():
            raise ValueError("System message cannot be empty.")

        session_id = self._validate_session(session_id)

        if self.log_messages:
            self._log(f"Changing system message for session `{session_id}`. New system message: `{system_message}`")

        new_system_message: Dict[str, str] = {"role": "system", "content": system_message}
        self.sessions[session_id][0] = new_system_message

        # Persist the updated system message to disk (atomic in _save_session_to_disk)
        self._save_session_to_disk(session_id)

    def get_conversation_history_as_text(self, session_id: Optional[str] = None) -> str:
        """
        Returns the conversation history as a formatted plain text string.

        Args:
            session_id (Optional[str], optional): ID of the session. Defaults to None.

        Returns:
            str: The formatted conversation history as plain text.
        """
        session_id = self._validate_session(session_id)

        if not self.sessions[session_id]:
            return ""

        history = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.sessions[session_id])
        return history

    def get_conversation_history(self, session_id: Optional[str] = None) -> List[dict]:
        """
        Returns the raw conversation history as an array.

        Args:
            session_id (Optional[str], optional): ID of the session. Defaults to None.

        Returns:
            list of dictionaries: The raw conversation history.
        """
        session_id = self._validate_session(session_id)

        if not self.sessions[session_id]:
            return []
        else:
            return self.sessions[session_id]

    def reset_conversation(self, session_id: Optional[str] = None) -> None:
        """
        Resets the conversation history to the default messages.

        Args:
            session_id (Optional[str], optional): ID of the session. Defaults to None.
        """
        session_id = self._validate_session(session_id)
        self._log(f"Resetting conversation for session `{session_id}`.")

        if len(self.sessions[session_id]) <= 1:  # Only system message exists
            self._log_warning(f"Session '{session_id}' is already at its default state.")

        self.sessions[session_id] = [self.sessions[session_id][0]]  # Preserve system message
        self._save_session_to_disk(session_id)

    def save_conversation(self, file_path: str, session_id: Optional[str] = None) -> None:
        """
        Saves the current conversation history.

        Args:
            file_path (str): The path to save the conversation history as a JSON file.
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.
        """
        session_id = self._validate_session(session_id)
        self._log(f"Saving conversation for session `{session_id}`.")

        with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
            json.dump(self.sessions[session_id], tmp_file)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_file.name, file_path)

    def load_conversation(self, file_path: str, session_id: Optional[str] = None) -> None:
        """
        Loads a conversation history from a JSON file.

        Args:
            file_path (str): The path to the JSON file containing the conversation history.
            session_id (Optional[str], optional): ID of the conversation session. Defaults to None.

        Raises:
            ValueError: If the loaded file is not valid or has an invalid JSON format.
        """
        session_id = self._validate_session(session_id)
        self._log(f"Loading conversation for session `{session_id}`.")

        try:
            with open(file_path, 'r') as f:
                loaded_session = json.load(f)
                if not isinstance(loaded_session, list):
                    raise ValueError("Invalid conversation format. Expected a list of messages.")

            self.sessions[session_id] = loaded_session
            self._session_locks.setdefault(session_id, asyncio.Lock())
            self._save_session_to_disk(session_id)
        except FileNotFoundError:
            self._log_warning(f"File '{file_path}' not found. Starting a fresh session for '{session_id}'.")
            self.reset_conversation(session_id)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in the conversation file.")
        except Exception as e:
            raise e

    async def _request_completion(self, message_content: str, session_id: Optional[str], timeout: int) -> str:
        """
        Internal function to handle synchronous and asynchronous requests to the OpenAI API.

        Args:
            message_content (str): The user's message.
            session_id (Optional[str]): ID of the conversation session.
            timeout (int): Request timeout in seconds.

        Returns:
            str: The LLM's response.

        Raises:
            ProviderError: Chat client based error.
            Exception: For any other unexpected errors.
        """
        session_id = self._validate_session(session_id)
        lock = self._session_locks.setdefault(session_id, asyncio.Lock())

        async with lock:
            if self.log_messages:
                self._log(f"Requesting completion for session `{session_id}`. Message `{message_content}`")

            if self.sessions[session_id][0].get("role") != "system":
                self.sessions[session_id].insert(0, self.default_system_message)

            new_message = {"role": "user", "content": message_content}
            new_message["content"] = self._strip_thinking_tags(new_message["content"])

            turn_events = [new_message]

            # Build a safe tuple of OpenAI timeout exception types (SDK versions differ)
            openai_timeout_exc = getattr(getattr(openai, "error", object()), "Timeout", None)
            timeout_excs = (asyncio.TimeoutError,) + ((openai_timeout_exc,) if isinstance(openai_timeout_exc, type) else ())

            try:
                # Construct initial outbound messages
                if self.include_message_history:
                    messages = list(self.sessions[session_id]) + list(turn_events)
                else:
                    # Still include the current session's system message for consistent behavior.
                    sys_msg = self.sessions[session_id][:1] if self.sessions.get(session_id) else [self.default_system_message]
                    messages = list(sys_msg) + [new_message]

                for _ in range(self.max_tool_rounds):
                    # Hand over available tools
                    if self.tools and self.tool_schemas:
                        extras = {"tools": self.tool_schemas, "tool_choice": "auto"} if self.tool_schemas else {}
                    else:
                        extras = {}

                    completion = await self.async_client.complete(
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        top_p=self.top_p,
                        frequency_penalty=self.frequency_penalty,
                        presence_penalty=self.presence_penalty,
                        timeout=timeout,
                        extras=extras
                    )

                    # Tool calls requested?
                    if completion.tool_calls:
                        # 1) append assistant tool-call message to the *outbound* messages and to our turn buffer
                        assistant_tool_msg = {
                            "role": "assistant",
                            "content": completion.text or "",
                            "tool_calls": completion.tool_calls,
                        }
                        messages.append(assistant_tool_msg)
                        turn_events.append(assistant_tool_msg)

                        # 2) run tools and append tool outputs (both outbound + turn buffer)
                        for tc in completion.tool_calls:
                            name = tc.get("function", {}).get("name")
                            args_json = tc.get("function", {}).get("arguments", "{}")

                            try:
                                args = json.loads(args_json) if args_json else {}
                            except Exception:
                                self._log_warning(
                                    f"Tool '{name}' received invalid JSON arguments; falling back to empty args."
                                )
                                args = {}

                            fn = self.tools.get(name) if self.tools else None
                            if not fn:
                                tool_output = json.dumps({"error": f"Unknown tool: {name}"})
                            else:
                                try:
                                    res = fn(**args)
                                    if inspect.isawaitable(res):
                                        res = await res
                                    tool_output = res if isinstance(res, str) else json.dumps(res)
                                except Exception as e:
                                    tool_output = json.dumps({"error": str(e)})

                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tc.get("id"),
                                "content": tool_output,
                            }
                            messages.append(tool_msg)
                            turn_events.append(tool_msg)

                        # Continue: ask the model again now that tool results are appended
                        continue

                    # No tool calls -> final response for this turn
                    response = completion.text or ""
                    response = self._strip_thinking_tags(response)

                    final_assistant_msg = {"role": "assistant", "content": response}
                    turn_events.append(final_assistant_msg)

                    # Persist in correct order
                    if self.include_message_history:
                        if self.store_tool_messages:
                            # store everything in the turn, including tool traces
                            self.sessions[session_id].extend(turn_events)
                        else:
                            # store only user + final assistant (and skip tool traces / tool-call assistants)
                            filtered = []
                            for m in turn_events:
                                if m.get("role") == "user":
                                    filtered.append(m)
                                elif m.get("role") == "assistant" and "tool_calls" not in m:
                                    filtered.append(m)
                            self.sessions[session_id].extend(filtered)

                        self._save_session_to_disk(session_id)

                    return response

                # If we get here, we exceeded tool rounds without a final response.
                raise ChatClientError(
                    f"Exceeded max_tool_rounds ({self.max_tool_rounds}) without producing a final answer."
                )

            # --- Timeout from asyncio or OpenAI directly ---
            except timeout_excs as e:
                self._log_error(f"The request timed out (timeout={timeout}).")
                self._log_exception(f"Original error: {e}")
                raise

            # --- Provider-specific error types ---
            except ProviderError as e:
                self._log_exception(f"Client provider error: {e.__str__}")
                raise

            # --- aiohttp-specific HTTP/connection errors ---
            except aiohttp.ClientResponseError as e:
                self._log_exception(f"HTTP Error {e.status}: {e.message}")
                raise ChatClientError() from e
            except aiohttp.ClientConnectionError as e:
                self._log_exception(f"Connection error while accessing OpenAI API: {e}")
                raise ChatClientError() from e

            # --- General issues ---
            except ValueError as e:
                self._log_exception(f"Invalid input: {e}")
                raise
            except Exception as e:
                self._log_exception(f"An unexpected error occurred: {e}")
                raise

    def _strip_thinking_tags(self, text: str) -> str:
        """
        Strips thinking tags from the provided text.

        Args:
            text (str): The text to clean.

        Returns:
            str: The cleaned text.
        """
        if not text or not self.strip_thinking:
            return text
        
        cleaned = self._thinking_re.sub("", text)

        # tidy up leftover blank lines/spaces
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned

    def _load_all_sessions_from_disk(self) -> None:
        """
        Loads all session files into memory.
        """
        self.sessions = {}

        for filename in os.listdir(self.SESSION_DIR):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove '.json'

                with open(os.path.join(self.SESSION_DIR, filename), "r") as file:
                    self.sessions[session_id] = json.load(file)

    def _save_session_to_disk(self, session_id: str) -> None:
        """
        Saves a session to a file.

        Args:
            session_id (str): ID of the conversation session.

        Raises:
            ValueError: If session ID is empty.
        """
        if not self.save_sessions_to_disk or not self.include_message_history:
            return

        if not session_id.strip():
            raise ValueError("Session ID cannot be empty.")

        filepath = os.path.join(self.SESSION_DIR, f"{session_id}.json")

        # Atomic write (temp file + fsync + replace) to avoid corrupted JSON on crash.
        with tempfile.NamedTemporaryFile("w", delete=False, dir=self.SESSION_DIR) as tmp_file:
            json.dump(self.sessions[session_id], tmp_file)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_name = tmp_file.name

        os.replace(tmp_name, filepath)

    def _validate_session(self, session_id: Optional[str] = None) -> str:
        """
        Validates the session ID and returns a valid session identifier.
        If the session does not exist, initializes it with the default system message.

        Args:
            session_id (Optional[str], optional): The session ID to validate. Defaults to None.

        Returns:
            str: A valid session ID.
        """
        session_id = session_id or "default"

        # Ensure lock exists even before creating the session.
        self._session_locks.setdefault(session_id, asyncio.Lock())

        if session_id not in self.sessions:
            self.sessions[session_id] = [self.default_system_message]
            self._save_session_to_disk(session_id)

        return session_id
