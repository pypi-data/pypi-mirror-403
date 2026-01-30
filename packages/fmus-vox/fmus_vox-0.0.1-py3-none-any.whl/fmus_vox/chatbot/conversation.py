"""
fmus_vox.chatbot.conversation - Conversation management for voice assistants.

This module provides the core conversation management functionality,
including message history, context management, and turn-taking.
"""

import enum
import time
import json
from typing import List, Dict, Any, Optional, Union, Callable

from fmus_vox.core.audio import Audio


class Role(enum.Enum):
    """Enumeration of possible message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class Message:
    """
    Represents a single message in a conversation.

    A message can contain text content, audio references, and metadata.
    """

    def __init__(
        self,
        content: str,
        role: Union[Role, str],
        audio: Optional[Audio] = None,
        timestamp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a conversation message.

        Args:
            content: Text content of the message.
            role: Role of the message sender (user, assistant, system).
            audio: Associated audio data (if applicable).
            timestamp: Unix timestamp of when the message was created.
            metadata: Additional metadata about the message.
        """
        self.content = content

        # Convert string role to enum if needed
        if isinstance(role, str):
            try:
                self.role = Role(role.lower())
            except ValueError:
                self.role = Role.USER  # Default to user if invalid
        else:
            self.role = role

        self.audio = audio
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary representation.

        Returns:
            Dictionary representation of the message.
        """
        result = {
            "content": self.content,
            "role": self.role.value,
            "timestamp": self.timestamp,
        }

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a Message from a dictionary representation.

        Args:
            data: Dictionary containing message data.

        Returns:
            Message instance.
        """
        return cls(
            content=data["content"],
            role=data["role"],
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {})
        )

    def __str__(self) -> str:
        """String representation of the message."""
        return f"{self.role.value}: {self.content}"


class Conversation:
    """
    Manages a conversation session with message history and context.

    This class handles the state of a conversation, including message
    history, user and system context, and integration with language models.
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        max_history: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
        llm_provider = None,  # Avoid circular import
    ):
        """
        Initialize a conversation session.

        Args:
            system_prompt: Initial system prompt to set context.
            max_history: Maximum number of messages to keep in history.
            metadata: Additional metadata about the conversation.
            llm_provider: LLM provider to use for generating responses.
        """
        self.messages: List[Message] = []
        self.max_history = max_history
        self.metadata = metadata or {}
        self.llm_provider = llm_provider
        self.on_new_message_callbacks: List[Callable[[Message], None]] = []

        # Set system prompt if provided
        if system_prompt:
            self.add_message(system_prompt, Role.SYSTEM)

    def add_message(
        self,
        content: str,
        role: Union[Role, str],
        audio: Optional[Audio] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a new message to the conversation.

        Args:
            content: Text content of the message.
            role: Role of the message sender.
            audio: Associated audio data (if applicable).
            metadata: Additional metadata about the message.

        Returns:
            The created Message object.
        """
        message = Message(
            content=content,
            role=role,
            audio=audio,
            metadata=metadata
        )

        self.messages.append(message)

        # Trim history if needed
        if len(self.messages) > self.max_history:
            # Always keep the first message (system prompt) if it exists
            if self.messages and self.messages[0].role == Role.SYSTEM:
                self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
            else:
                self.messages = self.messages[-self.max_history:]

        # Trigger callbacks
        for callback in self.on_new_message_callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"Error in message callback: {str(e)}")

        return message

    def add_user_message(
        self,
        content: str,
        audio: Optional[Audio] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a user message to the conversation.

        Args:
            content: Text content of the message.
            audio: Associated audio data (if applicable).
            metadata: Additional metadata about the message.

        Returns:
            The created Message object.
        """
        return self.add_message(content, Role.USER, audio, metadata)

    def add_assistant_message(
        self,
        content: str,
        audio: Optional[Audio] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add an assistant message to the conversation.

        Args:
            content: Text content of the message.
            audio: Associated audio data (if applicable).
            metadata: Additional metadata about the message.

        Returns:
            The created Message object.
        """
        return self.add_message(content, Role.ASSISTANT, audio, metadata)

    def add_system_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a system message to the conversation.

        Args:
            content: Text content of the message.
            metadata: Additional metadata about the message.

        Returns:
            The created Message object.
        """
        return self.add_message(content, Role.SYSTEM, None, metadata)

    def get_last_message(self, role: Optional[Role] = None) -> Optional[Message]:
        """
        Get the last message in the conversation, optionally filtered by role.

        Args:
            role: If provided, find the last message with this role.

        Returns:
            The last message, or None if no messages match the criteria.
        """
        if not self.messages:
            return None

        if role is None:
            return self.messages[-1]

        for msg in reversed(self.messages):
            if msg.role == role:
                return msg

        return None

    async def generate_response(
        self,
        user_message: Optional[str] = None,
        audio: Optional[Audio] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Message:
        """
        Generate a response to the current conversation.

        Args:
            user_message: Optional new user message to add before generating.
            audio: Associated audio for the user message.
            metadata: Additional metadata for the user message.
            **kwargs: Additional parameters to pass to the LLM provider.

        Returns:
            The generated assistant message.

        Raises:
            ValueError: If no LLM provider is configured.
        """
        if self.llm_provider is None:
            raise ValueError("No LLM provider configured for this conversation")

        # Add the user message if provided
        if user_message:
            self.add_user_message(user_message, audio, metadata)

        # Get the formatted messages for the provider
        messages_for_llm = self.get_messages_for_llm()

        # Generate the response
        response = await self.llm_provider.generate(messages_for_llm, **kwargs)

        # Add the response to the conversation
        return self.add_assistant_message(response)

    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """
        Format messages for sending to an LLM provider.

        Returns:
            List of message dictionaries in the format expected by LLM APIs.
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]

    def on_new_message(self, callback: Callable[[Message], None]) -> None:
        """
        Register a callback to be called when a new message is added.

        Args:
            callback: Function to call with the new message.
        """
        self.on_new_message_callbacks.append(callback)

    def clear_history(self, keep_system_prompt: bool = True) -> None:
        """
        Clear the conversation history.

        Args:
            keep_system_prompt: If True, retain the first system message.
        """
        if keep_system_prompt and self.messages and self.messages[0].role == Role.SYSTEM:
            self.messages = [self.messages[0]]
        else:
            self.messages = []

    def save_to_file(self, filepath: str) -> None:
        """
        Save the conversation to a file.

        Args:
            filepath: Path to save the conversation to.
        """
        data = {
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
            "timestamp": time.time()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Conversation':
        """
        Load a conversation from a file.

        Args:
            filepath: Path to load the conversation from.

        Returns:
            Loaded Conversation instance.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        conversation = cls(metadata=data.get("metadata", {}))

        for msg_data in data.get("messages", []):
            message = Message.from_dict(msg_data)
            conversation.messages.append(message)

        return conversation

    def __len__(self) -> int:
        """Return the number of messages in the conversation."""
        return len(self.messages)

    def __str__(self) -> str:
        """Return a string representation of the conversation."""
        if not self.messages:
            return "Empty conversation"

        return "\n".join(str(msg) for msg in self.messages)
