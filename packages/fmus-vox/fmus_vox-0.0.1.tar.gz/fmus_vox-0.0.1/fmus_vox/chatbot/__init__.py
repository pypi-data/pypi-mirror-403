"""
fmus_vox.chatbot - Conversational AI interfaces and implementations.

This module provides functionality for building voice-based conversational
agents and integrating with language models for natural language understanding.
"""

import os
from typing import List, Dict, Any, Optional
from .conversation import Conversation, Message, Role
from .llm import LLMProvider, OpenAIProvider, AnthropicProvider
from .agents import Agent, LLMAgent, ToolAgent, VoiceAgent, create_agent

__all__ = [
    "Conversation",
    "Message",
    "Role",
    "LLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "chat",
    "Agent",
    "LLMAgent",
    "ToolAgent",
    "VoiceAgent",
    "create_agent",
]


def chat(message: str, context: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Simple chat function for quick conversational responses.

    This is a convenience function that provides a simple way to get
    chatbot responses without setting up a full Conversation object.

    Args:
        message: User message to respond to
        context: Optional list of previous messages for context

    Returns:
        Chatbot response text

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")

    # Create LLM provider and conversation
    llm_provider = OpenAIProvider(api_key=api_key)
    conversation = Conversation(llm_provider=llm_provider)

    # Add context messages if provided
    if context:
        for msg in context:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation.add_message(content, role)

    # Get response (note: this is async, so we need to handle it)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(conversation.generate_response(message))
    return result.content
