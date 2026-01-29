"""
ChatTzafon - LangChain chat model for Tzafon's AI models.

This module provides a LangChain-compatible chat model that integrates with
Tzafon's OpenAI-compatible chat completions API.
"""

from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
)

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from openai import OpenAI
from pydantic import Field, SecretStr

from langchain_tzafon.constants import Settings
from langchain_tzafon.utils import get_logger

logger = get_logger(__name__)
config = Settings()


class ChatTzafon(BaseChatModel):
    """LangChain chat model for Tzafon's AI models.

    This class provides integration with Tzafon's OpenAI-compatible chat
    completions API, supporting both synchronous generation and streaming.

    Example:
        >>> from langchain_tzafon import ChatTzafon
        >>> chat = ChatTzafon(model="tzafon.sm-1")
        >>> response = chat.invoke("Hello, how are you?")
        >>> print(response.content)

    Attributes:
        model: The Tzafon model to use. Defaults to "tzafon.sm-1".
        temperature: Sampling temperature between 0 and 1. Defaults to 0.7.
        max_tokens: Maximum number of tokens to generate.
        stop: List of stop sequences.
        api_key: Tzafon API key. Falls back to TZAFON_API_KEY env var.
        base_url: Base URL for the Tzafon API.
    """

    model: str = Field(default="tzafon.sm-1", description="Tzafon model to use")
    temperature: float = Field(
        default=0.7, ge=0, le=1, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate"
    )
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    api_key: Optional[SecretStr] = Field(default=None, description="Tzafon API key")
    base_url: str = Field(
        default="https://api.tzafon.ai/v1",
        description="Base URL for Tzafon API",
    )

    _client: Optional[OpenAI] = None

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the ChatTzafon model."""
        super().__init__(**kwargs)
        # Get API key from constructor or environment
        if self.api_key is None:
            env_key = config.api_key.get_secret_value()
            if env_key:
                self.api_key = SecretStr(env_key)

        if self.api_key is None:
            raise ValueError(
                "Tzafon API key is required. Pass api_key parameter or set "
                "TZAFON_API_KEY environment variable."
            )

        self._client = OpenAI(
            api_key=self.api_key.get_secret_value(),
            base_url=self.base_url,
        )

    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return "tzafon-chat"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters for this model."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url,
        }

    def _convert_messages_to_openai_format(
        self, messages: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenAI message format.

        Args:
            messages: List of LangChain messages.

        Returns:
            List of messages in OpenAI format.
        """
        openai_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                # Default to user for unknown message types
                role = "user"

            openai_messages.append(
                {
                    "role": role,
                    "content": str(message.content),
                }
            )

        return openai_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat completion.

        Args:
            messages: List of messages to send.
            stop: Optional list of stop sequences.
            run_manager: Optional callback manager.
            **kwargs: Additional arguments passed to the API.

        Returns:
            ChatResult containing the generated response.
        """
        openai_messages = self._convert_messages_to_openai_format(messages)

        # Merge stop sequences
        stop_sequences = stop or self.stop

        response = self._client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop_sequences,
            stream=False,
            **kwargs,
        )

        # Extract the response content
        choice = response.choices[0]
        content = choice.message.content or ""

        # Build usage metadata if available
        llm_output = {}
        if response.usage:
            llm_output["token_usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        llm_output["model_name"] = response.model

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=content),
                    generation_info={"finish_reason": choice.finish_reason},
                )
            ],
            llm_output=llm_output,
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream a chat completion.

        Args:
            messages: List of messages to send.
            stop: Optional list of stop sequences.
            run_manager: Optional callback manager.
            **kwargs: Additional arguments passed to the API.

        Yields:
            ChatGenerationChunk for each streamed token.
        """
        openai_messages = self._convert_messages_to_openai_format(messages)

        # Merge stop sequences
        stop_sequences = stop or self.stop

        stream = self._client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop_sequences,
            stream=True,
            **kwargs,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=content),
                    generation_info={
                        "finish_reason": chunk.choices[0].finish_reason,
                    },
                )

                if run_manager:
                    run_manager.on_llm_new_token(content)
