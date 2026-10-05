"""
LLM client module for AI-powered suggestions.

Provides interface to call LLM APIs for folder organization suggestions.
Currently supports ApiFreeLLM, with extensible architecture for other providers.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests

from organiser.config import Config


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Subclasses must implement the generate_response method.
    """

    def __init__(self, config: Config):
        self.config = config

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            LLM response text.

        Raises:
            LLMClientError: If the API call fails after retries.
        """
        pass


class ApiFreeLLMClient(LLMClient):
    """
    Client for ApiFreeLLM API.

    Features:
    - Automatic retry with rate limiting
    - Timeout handling
    - Error reporting
    """

    def __init__(self, config: Config):
        super().__init__(config)
        if not config.api_key:
            raise ValueError(
                "API key is required. Set AI_FOLDER_ORG_API_KEY environment variable "
                "or provide it in config file."
            )

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response using ApiFreeLLM.

        Args:
            prompt: The prompt to send.

        Returns:
            LLM response text.

        Raises:
            LLMClientError: If all retries fail.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        data = {
            "message": prompt,
            "model": self.config.model,
        }

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                resp = requests.post(
                    self.config.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.config.timeout_seconds,
                )
                resp.raise_for_status()
                result = resp.json()

                # Extract response from various possible formats
                if "response" in result:
                    return result["response"]
                elif "message" in result:
                    return result["message"]
                else:
                    return str(result)

            except requests.Timeout:
                last_error = f"Request timed out after {self.config.timeout_seconds}s"
                print(f"API error (attempt {attempt + 1}): {last_error}")
            except requests.RequestException as e:
                last_error = f"Request failed: {e}"
                print(f"API error (attempt {attempt + 1}): {e}")
            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON response: {e}"
                print(f"API error (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                print(f"API error (attempt {attempt + 1}): {e}")

            # Rate limiting between retries
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.rate_limit_seconds)

        raise LLMClientError(
            f"Failed to get response from ApiFreeLLM after {self.config.max_retries} retries. "
            f"Last error: {last_error}"
        )


class MockLLMClient(LLMClient):
    """
    Mock client for testing purposes.

    Returns predefined responses for testing without calling actual API.
    """

    def __init__(self, config: Config, mock_response: str = "{}"):
        super().__init__(config)
        self.mock_response = mock_response

    def generate_response(self, prompt: str) -> str:
        """Return mock response."""
        return self.mock_response


def create_client(config: Config, client_type: str = "apifreellm") -> LLMClient:
    """
    Factory function to create LLM clients.

    Args:
        client_type: Type of client to create ("apifreellm", "mock").
        config: Configuration object.

    Returns:
        LLMClient instance.

    Raises:
        ValueError: If unknown client type.
    """
    clients = {
        "apifreellm": ApiFreeLLMClient,
        "mock": MockLLMClient,
    }

    if client_type not in clients:
        raise ValueError(f"Unknown client type: {client_type}. "
                        f"Available: {list(clients.keys())}")

    return clients[client_type](config)
