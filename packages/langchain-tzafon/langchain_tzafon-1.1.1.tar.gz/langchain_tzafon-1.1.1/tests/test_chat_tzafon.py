"""
Unit tests for ChatTzafon.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain_tzafon.chat_tzafon import ChatTzafon


@pytest.fixture
def mock_settings():
    """Mock the settings configuration."""
    with patch("langchain_tzafon.chat_tzafon.config") as mock_config:
        mock_config.api_key.get_secret_value.return_value = "test_api_key"
        yield mock_config


@pytest.fixture
def mock_openai_client():
    """Mock the OpenAI client."""
    with patch("langchain_tzafon.chat_tzafon.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        yield mock_client


class TestChatTzafonInitialization:
    """Tests for ChatTzafon initialization."""

    def test_initialization_with_api_key(self, mock_settings, mock_openai_client):
        """Test that ChatTzafon initializes with explicit API key."""
        chat = ChatTzafon(api_key="explicit_key")
        assert chat.api_key.get_secret_value() == "explicit_key"
        assert chat.model == "tzafon.sm-1"
        assert chat.temperature == 0.7

    def test_initialization_from_env(self, mock_settings, mock_openai_client):
        """Test that ChatTzafon falls back to environment variable."""
        chat = ChatTzafon()
        assert chat.api_key.get_secret_value() == "test_api_key"

    def test_initialization_missing_key_raises(self):
        """Test that missing API key raises ValueError."""
        with patch("langchain_tzafon.chat_tzafon.config") as mock_config:
            mock_config.api_key.get_secret_value.return_value = ""
            with pytest.raises(ValueError, match="Tzafon API key is required"):
                ChatTzafon()

    def test_custom_model_and_params(self, mock_settings, mock_openai_client):
        """Test initialization with custom model and parameters."""
        chat = ChatTzafon(
            model="tzafon.northstar.cua.sft",
            temperature=0.5,
            max_tokens=1024,
            stop=["<|end|>"],
        )
        assert chat.model == "tzafon.northstar.cua.sft"
        assert chat.temperature == 0.5
        assert chat.max_tokens == 1024
        assert chat.stop == ["<|end|>"]


class TestMessageConversion:
    """Tests for message conversion to OpenAI format."""

    def test_convert_human_message(self, mock_settings, mock_openai_client):
        """Test conversion of HumanMessage."""
        chat = ChatTzafon()
        messages = [HumanMessage(content="Hello")]
        result = chat._convert_messages_to_openai_format(messages)
        assert result == [{"role": "user", "content": "Hello"}]

    def test_convert_ai_message(self, mock_settings, mock_openai_client):
        """Test conversion of AIMessage."""
        chat = ChatTzafon()
        messages = [AIMessage(content="Hi there!")]
        result = chat._convert_messages_to_openai_format(messages)
        assert result == [{"role": "assistant", "content": "Hi there!"}]

    def test_convert_system_message(self, mock_settings, mock_openai_client):
        """Test conversion of SystemMessage."""
        chat = ChatTzafon()
        messages = [SystemMessage(content="You are helpful.")]
        result = chat._convert_messages_to_openai_format(messages)
        assert result == [{"role": "system", "content": "You are helpful."}]

    def test_convert_mixed_messages(self, mock_settings, mock_openai_client):
        """Test conversion of mixed message types."""
        chat = ChatTzafon()
        messages = [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi!"),
            HumanMessage(content="How are you?"),
        ]
        result = chat._convert_messages_to_openai_format(messages)
        assert result == [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"},
        ]


class TestGenerate:
    """Tests for the _generate method."""

    def test_generate_returns_chat_result(self, mock_settings, mock_openai_client):
        """Test that _generate returns a valid ChatResult."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help?"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "tzafon.sm-1"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_openai_client.chat.completions.create.return_value = mock_response

        chat = ChatTzafon()
        messages = [HumanMessage(content="Hello")]
        result = chat._generate(messages)

        assert len(result.generations) == 1
        assert result.generations[0].message.content == "Hello! How can I help?"
        assert result.llm_output["token_usage"]["total_tokens"] == 15

    def test_generate_calls_api_with_correct_params(
        self, mock_settings, mock_openai_client
    ):
        """Test that _generate calls the API with correct parameters."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "tzafon.sm-1"
        mock_response.usage = None
        mock_openai_client.chat.completions.create.return_value = mock_response

        chat = ChatTzafon(temperature=0.5, max_tokens=100)
        messages = [HumanMessage(content="Test")]
        chat._generate(messages, stop=["<|end|>"])

        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "tzafon.sm-1"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["stop"] == ["<|end|>"]
        assert call_kwargs["stream"] is False


class TestStream:
    """Tests for the _stream method."""

    def test_stream_yields_chunks(self, mock_settings, mock_openai_client):
        """Test that _stream yields ChatGenerationChunks."""
        # Setup mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk1.choices[0].finish_reason = None

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = " world"
        mock_chunk2.choices[0].finish_reason = "stop"

        mock_openai_client.chat.completions.create.return_value = iter(
            [mock_chunk1, mock_chunk2]
        )

        chat = ChatTzafon()
        messages = [HumanMessage(content="Test")]
        chunks = list(chat._stream(messages))

        assert len(chunks) == 2
        assert chunks[0].message.content == "Hello"
        assert chunks[1].message.content == " world"

    def test_stream_calls_api_with_stream_true(self, mock_settings, mock_openai_client):
        """Test that _stream calls API with stream=True."""
        mock_openai_client.chat.completions.create.return_value = iter([])

        chat = ChatTzafon()
        messages = [HumanMessage(content="Test")]
        list(chat._stream(messages))  # Consume the iterator

        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["stream"] is True


class TestLLMType:
    """Tests for ChatTzafon properties."""

    def test_llm_type(self, mock_settings, mock_openai_client):
        """Test that _llm_type returns correct value."""
        chat = ChatTzafon()
        assert chat._llm_type == "tzafon-chat"

    def test_identifying_params(self, mock_settings, mock_openai_client):
        """Test that _identifying_params returns model info."""
        chat = ChatTzafon(model="tzafon.sm-1", temperature=0.8, max_tokens=500)
        params = chat._identifying_params
        assert params["model"] == "tzafon.sm-1"
        assert params["temperature"] == 0.8
        assert params["max_tokens"] == 500
