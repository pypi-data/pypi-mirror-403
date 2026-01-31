"""Tests for Message class."""

import pytest
from unittest.mock import Mock
from march_agent.message import Message
from march_agent.conversation import Conversation


class TestMessageInitialization:
    """Test Message initialization."""

    def test_message_initialization(self):
        """Test direct message instantiation."""
        message = Message(
            content="Test content",
            conversation_id="conv-123",
            headers={"conversationId": "conv-123", "from_": "user"},
            raw_body={"content": "Test content"}
        )

        assert message.content == "Test content"
        assert message.conversation_id == "conv-123"
        assert message.headers == {"conversationId": "conv-123", "from_": "user"}
        assert message.raw_body == {"content": "Test content"}
        assert message.conversation is None

    def test_from_kafka_message(self, mock_conversation_client):
        """Test creating message from Kafka message."""
        body = {"content": "Hello world"}
        headers = {
            "conversationId": "conv-456",
            "from_": "user",
            "custom_header": "value"
        }

        message = Message.from_kafka_message(
            body, headers, conversation_client=mock_conversation_client
        )

        assert message.content == "Hello world"
        assert message.conversation_id == "conv-456"
        assert message.headers == headers
        assert message.raw_body == body

    def test_from_kafka_message_extracts_content(self):
        """Test content extraction from message body."""
        body = {"content": "Test message", "extra": "data"}
        headers = {"conversationId": "conv-123"}

        message = Message.from_kafka_message(body, headers)

        assert message.content == "Test message"

    def test_from_kafka_message_extracts_conversation_id(self):
        """Test conversation ID extraction from headers."""
        body = {"content": "Test"}
        headers = {"conversationId": "conv-789", "other": "header"}

        message = Message.from_kafka_message(body, headers)

        assert message.conversation_id == "conv-789"

    def test_from_kafka_message_stores_headers(self):
        """Test all headers are preserved."""
        body = {"content": "Test"}
        headers = {
            "conversationId": "conv-123",
            "from_": "user",
            "custom1": "value1",
            "custom2": "value2"
        }

        message = Message.from_kafka_message(body, headers)

        assert message.headers == headers
        assert "custom1" in message.headers
        assert "custom2" in message.headers

    def test_from_kafka_message_stores_raw_body(self):
        """Test raw body is preserved."""
        body = {
            "content": "Test",
            "metadata": {"key": "value"},
            "extra_field": 123
        }
        headers = {"conversationId": "conv-123"}

        message = Message.from_kafka_message(body, headers)

        assert message.raw_body == body
        assert "metadata" in message.raw_body
        assert "extra_field" in message.raw_body

    def test_conversation_creation(self, mock_conversation_client):
        """Test conversation is created when conversation_id is present."""
        body = {"content": "Test"}
        headers = {"conversationId": "conv-123"}

        message = Message.from_kafka_message(
            body, headers, conversation_client=mock_conversation_client
        )

        # Conversation should be created immediately
        assert message.conversation is not None
        assert isinstance(message.conversation, Conversation)
        assert message.conversation.id == "conv-123"

    def test_conversation_without_client(self):
        """Test conversation is None when no client provided."""
        body = {"content": "Test"}
        headers = {"conversationId": "conv-123"}

        message = Message.from_kafka_message(body, headers, conversation_client=None)

        # Conversation should be None
        assert message.conversation is None
