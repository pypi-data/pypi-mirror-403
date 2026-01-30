"""
fmus_vox.chatbot.llm - Language model provider implementations.

This module provides interfaces and implementations for interacting with
various language model APIs for generating conversational responses.
"""

import abc
import json
import httpx
from typing import List, Dict, Any, Optional, Union


class LLMProvider(abc.ABC):
    """
    Abstract base class for language model providers.

    This class defines the interface that all LLM providers must implement.
    """

    @abc.abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate a response from the language model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Generated text response.
        """
        pass

    @abc.abstractmethod
    async def generate_with_streaming(
        self,
        messages: List[Dict[str, str]],
        callback,
        **kwargs
    ) -> str:
        """
        Generate a response with streaming.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            callback: Function to call with each chunk of generated text.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Complete generated text response.
        """
        pass


class OpenAIProvider(LLMProvider):
    """
    Language model provider using OpenAI's API.

    This provider interfaces with OpenAI's chat completion API to
    generate responses for conversations.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model: Model identifier to use (e.g., 'gpt-3.5-turbo').
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0-2).
            base_url: Alternative API base URL for compatible services.
            **kwargs: Additional parameters to pass to the API.
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url = base_url or "https://api.openai.com/v1"
        self.default_params = kwargs

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate a response from the OpenAI API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Generated text response.

        Raises:
            Exception: If the API request fails.
        """
        # Combine default params with call-specific params
        params = self.default_params.copy()
        params.update(kwargs)

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            **params
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")

            result = response.json()

            # Extract the response text
            try:
                return result["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise Exception(f"Failed to parse OpenAI response: {str(e)}")

    async def generate_with_streaming(
        self,
        messages: List[Dict[str, str]],
        callback,
        **kwargs
    ) -> str:
        """
        Generate a response with streaming.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            callback: Function to call with each chunk of generated text.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Complete generated text response.

        Raises:
            Exception: If the API request fails.
        """
        # Combine default params with call-specific params
        params = self.default_params.copy()
        params.update(kwargs)

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
            **params
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        full_response = ""

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {await response.text()}")

                # Process the streaming response
                async for line in response.aiter_lines():
                    if not line.strip() or line.strip() == "data: [DONE]":
                        continue

                    if line.startswith("data: "):
                        json_line = line[6:].strip()
                        try:
                            chunk = json.loads(json_line)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                full_response += content
                                callback(content)
                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            print(f"Error parsing streaming response: {str(e)}")

        return full_response


class AnthropicProvider(LLMProvider):
    """
    Language model provider using Anthropic's API.

    This provider interfaces with Anthropic's Claude model to
    generate responses for conversations.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-2",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model: Model identifier to use (e.g., 'claude-2').
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0-1).
            **kwargs: Additional parameters to pass to the API.
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.default_params = kwargs

    def _format_messages_for_anthropic(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages for the Anthropic API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.

        Returns:
            Formatted conversation string for Anthropic.
        """
        formatted = ""

        for msg in messages:
            role = msg["role"].lower()
            content = msg["content"]

            if role == "system":
                # System messages are added as human instructions
                formatted += f"Human: <system>{content}</system>\n\n"
            elif role == "user" or role == "human":
                formatted += f"Human: {content}\n\n"
            elif role == "assistant" or role == "ai":
                formatted += f"Assistant: {content}\n\n"

        # Add final Assistant prompt
        formatted += "Assistant: "

        return formatted

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate a response from the Anthropic API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Generated text response.

        Raises:
            Exception: If the API request fails.
        """
        # Combine default params with call-specific params
        params = self.default_params.copy()
        params.update(kwargs)

        # Format messages for Anthropic
        prompt = self._format_messages_for_anthropic(messages)

        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": self.max_tokens,
            "temperature": self.temperature,
            **params
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/complete",
                headers=headers,
                json=payload,
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.text}")

            result = response.json()

            # Extract the response text
            try:
                return result["completion"]
            except KeyError as e:
                raise Exception(f"Failed to parse Anthropic response: {str(e)}")

    async def generate_with_streaming(
        self,
        messages: List[Dict[str, str]],
        callback,
        **kwargs
    ) -> str:
        """
        Generate a response with streaming.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            callback: Function to call with each chunk of generated text.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Complete generated text response.

        Raises:
            Exception: If the API request fails.
        """
        # Combine default params with call-specific params
        params = self.default_params.copy()
        params.update(kwargs)

        # Format messages for Anthropic
        prompt = self._format_messages_for_anthropic(messages)

        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
            **params
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        full_response = ""

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/complete",
                headers=headers,
                json=payload,
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"Anthropic API error: {await response.text()}")

                # Process the streaming response
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    if line.startswith("data: "):
                        json_line = line[6:].strip()
                        try:
                            chunk = json.loads(json_line)
                            if "completion" in chunk:
                                content = chunk["completion"]
                                if content:
                                    # We need to determine the delta from the full response
                                    delta = content[len(full_response):]
                                    full_response = content
                                    if delta:
                                        callback(delta)
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Error parsing streaming response: {str(e)}")

        return full_response
