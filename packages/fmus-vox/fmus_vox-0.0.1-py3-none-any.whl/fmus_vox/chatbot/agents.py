"""
Agent implementation for fmus-vox chatbot functionality.

This module provides agent-based chatbot implementations that can
handle complex conversational flows and multi-turn interactions.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from abc import ABC, abstractmethod

from fmus_vox.core.audio import Audio
from fmus_vox.chatbot.conversation import Conversation, Message, Role
from fmus_vox.chatbot.llm import LLMProvider
from fmus_vox.core.utils import get_logger


class Agent(ABC):
    """
    Abstract base class for conversational agents.

    Agents provide higher-level conversational capabilities beyond
    simple chat interfaces, including tools, memory, and planning.

    Args:
        name: Agent name
        description: Agent description
        **kwargs: Additional agent parameters
    """

    def __init__(
        self,
        name: str = "Assistant",
        description: str = "A helpful assistant",
        **kwargs
    ):
        """
        Initialize the agent.

        Args:
            name: Agent name
            description: Agent description
            **kwargs: Additional agent parameters
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # Conversation management
        self._conversations: Dict[str, Conversation] = {}

    @abstractmethod
    async def respond(
        self,
        message: str,
        conversation_id: str = "default",
        **kwargs
    ) -> str:
        """
        Generate a response to a user message.

        Args:
            message: User message
            conversation_id: ID of the conversation
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        pass

    def get_conversation(self, conversation_id: str = "default") -> Conversation:
        """
        Get or create a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation object
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = Conversation()

        return self._conversations[conversation_id]

    def clear_conversation(self, conversation_id: str = "default") -> None:
        """
        Clear a conversation's history.

        Args:
            conversation_id: ID of the conversation
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]


class LLMAgent(Agent):
    """
    Agent powered by an LLM provider.

    This agent uses a language model to generate responses and
    can be customized with system prompts and parameters.

    Args:
        llm_provider: LLM provider to use
        system_prompt: System prompt for the agent
        name: Agent name
        description: Agent description
        **kwargs: Additional agent parameters
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        system_prompt: Optional[str] = None,
        name: str = "Assistant",
        description: str = "A helpful assistant",
        **kwargs
    ):
        """
        Initialize the LLM agent.

        Args:
            llm_provider: LLM provider to use
            system_prompt: System prompt for the agent
            name: Agent name
            description: Agent description
            **kwargs: Additional agent parameters
        """
        super().__init__(name=name, description=description, **kwargs)

        self.llm_provider = llm_provider

        # Create conversation with system prompt
        default_system = f"You are {name}. {description}"
        self._system_prompt = system_prompt or default_system

    async def respond(
        self,
        message: str,
        conversation_id: str = "default",
        **kwargs
    ) -> str:
        """
        Generate a response to a user message.

        Args:
            message: User message
            conversation_id: ID of the conversation
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        conversation = self.get_conversation(conversation_id)

        # Set system prompt if this is a new conversation
        if len(conversation) == 0:
            conversation.add_system_message(self._system_prompt)

        # Generate response
        result = await conversation.generate_response(message)

        return result.content


class ToolAgent(Agent):
    """
    Agent that can use tools to accomplish tasks.

    This agent can call external tools/APIs to gather information
    or perform actions during the conversation.

    Args:
        llm_provider: LLM provider to use
        tools: List of available tools
        system_prompt: System prompt for the agent
        name: Agent name
        description: Agent description
        **kwargs: Additional agent parameters
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        name: str = "Assistant",
        description: str = "A helpful assistant with tools",
        **kwargs
    ):
        """
        Initialize the tool agent.

        Args:
            llm_provider: LLM provider to use
            tools: List of available tools
            system_prompt: System prompt for the agent
            name: Agent name
            description: Agent description
            **kwargs: Additional agent parameters
        """
        super().__init__(name=name, description=description, **kwargs)

        self.llm_provider = llm_provider
        self.tools = tools or []
        self._tool_map = {tool["name"]: tool for tool in self.tools}

        default_system = self._build_system_prompt(system_prompt)
        self._system_prompt = default_system

    def _build_system_prompt(self, custom_prompt: Optional[str]) -> str:
        """Build the system prompt with tool information."""
        base_prompt = f"You are {self.name}. {self.description}."

        if self.tools:
            tool_desc = "\n\nYou have access to the following tools:\n"
            for tool in self.tools:
                tool_desc += f"- {tool['name']}: {tool.get('description', 'No description')}\n"

            tool_desc += "\nTo use a tool, respond in the format: USE_TOOL[{tool_name}]: {parameters}"
            base_prompt += tool_desc

        if custom_prompt:
            base_prompt += f"\n\n{custom_prompt}"

        return base_prompt

    async def respond(
        self,
        message: str,
        conversation_id: str = "default",
        **kwargs
    ) -> str:
        """
        Generate a response to a user message, using tools if needed.

        Args:
            message: User message
            conversation_id: ID of the conversation
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        conversation = self.get_conversation(conversation_id)

        # Set system prompt if this is a new conversation
        if len(conversation) == 0:
            conversation.add_system_message(self._system_prompt)

        # Check if the agent wants to use a tool
        response = await self._generate_with_tools(conversation, message)

        # Handle tool use
        while response.startswith("USE_TOOL["):
            response = await self._execute_tool(conversation, response)

        return response

    async def _generate_with_tools(
        self,
        conversation: Conversation,
        message: str
    ) -> str:
        """Generate a response that may include tool use."""
        # Add user message
        conversation.add_user_message(message)

        # Generate response
        messages = conversation.get_messages_for_llm()
        response = await self.llm_provider.generate(messages)

        return response.strip()

    async def _execute_tool(
        self,
        conversation: Conversation,
        tool_call: str
    ) -> str:
        """Execute a tool call and generate a follow-up response."""
        # Parse tool call
        # Format: USE_TOOL[tool_name]: parameters
        try:
            tool_name_end = tool_call.index("]")
            tool_name = tool_call[9:tool_name_end]  # Skip "USE_TOOL["
            parameters = tool_call[tool_name_end + 2:].strip()  # Skip "]: "

            # Get tool
            tool = self._tool_map.get(tool_name)
            if not tool:
                return f"Error: Unknown tool '{tool_name}'"

            # Execute tool
            tool_func = tool["function"]
            if asyncio.iscoroutinefunction(tool_func):
                tool_result = await tool_func(**self._parse_parameters(parameters))
            else:
                tool_result = tool_func(**self._parse_parameters(parameters))

            # Add tool result to conversation
            conversation.add_assistant_message(
                f"Used tool {tool_name}. Result: {tool_result}"
            )

            # Generate follow-up response
            messages = conversation.get_messages_for_llm()
            response = await self.llm_provider.generate(messages)

            return response.strip()

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return f"Error executing tool: {str(e)}"

    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """Parse tool parameters from string."""
        # Simple parsing - for more complex cases, use json.loads
        try:
            import json
            return json.loads(params_str)
        except:
            # Treat as single string parameter
            return {"input": params_str}


class VoiceAgent(Agent):
    """
    Agent specialized for voice interactions.

    This agent is optimized for voice conversations with features
    like shorter responses, natural language, and speech-specific behaviors.

    Args:
        llm_provider: LLM provider to use
        system_prompt: System prompt for the agent
        max_response_length: Maximum length of responses
        name: Agent name
        description: Agent description
        **kwargs: Additional agent parameters
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        system_prompt: Optional[str] = None,
        max_response_length: int = 100,
        name: str = "Voice Assistant",
        description: str = "A helpful voice assistant",
        **kwargs
    ):
        """
        Initialize the voice agent.

        Args:
            llm_provider: LLM provider to use
            system_prompt: System prompt for the agent
            max_response_length: Maximum length of responses
            name: Agent name
            description: Agent description
            **kwargs: Additional agent parameters
        """
        super().__init__(name=name, description=description, **kwargs)

        self.llm_provider = llm_provider
        self.max_response_length = max_response_length

        # Voice-optimized system prompt
        default_system = f"""You are {name}, a voice assistant. {description}

Keep your responses:
- Short and concise (under {max_response_length} words)
- Natural and conversational
- Suitable for spoken communication
- Friendly and engaging

Avoid using:
- Long lists or enumerations
- Complex technical jargon
- Markdown formatting
- Written conventions like asterisks for emphasis"""

        self._system_prompt = system_prompt or default_system

    async def respond(
        self,
        message: str,
        conversation_id: str = "default",
        **kwargs
    ) -> str:
        """
        Generate a response optimized for voice output.

        Args:
            message: User message
            conversation_id: ID of the conversation
            **kwargs: Additional parameters

        Returns:
            Voice-optimized response
        """
        conversation = self.get_conversation(conversation_id)

        # Set system prompt if this is a new conversation
        if len(conversation) == 0:
            conversation.add_system_message(self._system_prompt)

        # Generate response
        result = await conversation.generate_response(message)

        # Clean up for voice output
        response = self._clean_for_voice(result.content)

        return response

    def _clean_for_voice(self, text: str) -> str:
        """
        Clean text for voice output.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove markdown
        text = text.replace("**", "").replace("*", "")
        text = text.replace("#", "").replace("`", "")

        # Clean up URLs
        import re
        text = re.sub(r'https?://\S+', 'a link', text)

        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text


def create_agent(
    agent_type: str = "llm",
    llm_provider: Optional[LLMProvider] = None,
    **kwargs
) -> Agent:
    """
    Factory function to create agents.

    Args:
        agent_type: Type of agent (llm, tool, voice)
        llm_provider: LLM provider to use
        **kwargs: Additional agent parameters

    Returns:
        Agent instance
    """
    if agent_type == "llm":
        if not llm_provider:
            raise ValueError("llm_provider required for llm agent")
        return LLMAgent(llm_provider=llm_provider, **kwargs)
    elif agent_type == "tool":
        if not llm_provider:
            raise ValueError("llm_provider required for tool agent")
        return ToolAgent(llm_provider=llm_provider, **kwargs)
    elif agent_type == "voice":
        if not llm_provider:
            raise ValueError("llm_provider required for voice agent")
        return VoiceAgent(llm_provider=llm_provider, **kwargs)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
