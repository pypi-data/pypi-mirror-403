# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_synthesis

"""
OpenAI client module.

This module provides the client interface for interacting with OpenAI
services for text generation (TeacherModel) and embedding generation (EmbeddingService).
"""

import json
from typing import List, Optional, Type, cast

import httpx

from coreason_synthesis.interfaces import EmbeddingService, T, TeacherModel


class OpenAITeacherModel(TeacherModel):
    """Concrete implementation of the Teacher Model using OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 60,
        client: Optional[httpx.AsyncClient] = None,
    ):
        """Initializes the OpenAITeacherModel.

        Args:
            api_key: OpenAI API key.
            model: The model identifier to use.
            base_url: Base URL for OpenAI API.
            timeout: Request timeout.
            client: Optional existing httpx.AsyncClient.
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        self._internal_client = client is None
        self._client = client or httpx.AsyncClient(headers=headers, timeout=timeout)
        # Ensure headers are set if client was provided
        self._client.headers.update(headers)

    async def close(self) -> None:
        """Closes the underlying HTTP client if it was created internally."""
        if self._internal_client:
            await self._client.aclose()

    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generates text based on a prompt and optional context.

        Args:
            prompt: The main prompt.
            context: Optional context to be prepended.

        Returns:
            The generated text.
        """
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
        }

        response = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return cast(str, content)

    async def generate_structured(self, prompt: str, response_model: Type[T], context: Optional[str] = None) -> T:
        """Generates a structured object based on a prompt and optional context.

        Uses JSON mode to ensure output conforms to the Pydantic model.

        Args:
            prompt: The main prompt.
            response_model: The Pydantic model class.
            context: Optional background context.

        Returns:
            An instance of the response_model.
        """
        # Create a system prompt enforcing JSON output
        system_msg = "You are a helpful assistant that outputs JSON."
        if context:
            system_msg += f"\nContext:\n{context}"

        # Add schema instruction
        schema = response_model.model_json_schema()
        user_msg = f"{prompt}\n\nReturn the result as a valid JSON object matching this schema:\n{json.dumps(schema)}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }

        response = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Parse JSON and validate with Pydantic
        parsed_data = json.loads(content)
        return response_model.model_validate(parsed_data)


class OpenAIEmbeddingService(EmbeddingService):
    """Concrete implementation of the Embedding Service using OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 30,
        client: Optional[httpx.AsyncClient] = None,
    ):
        """Initializes the OpenAIEmbeddingService.

        Args:
            api_key: OpenAI API key.
            model: The model identifier to use.
            base_url: Base URL for OpenAI API.
            timeout: Request timeout.
            client: Optional existing httpx.AsyncClient.
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        self._internal_client = client is None
        self._client = client or httpx.AsyncClient(headers=headers, timeout=timeout)
        self._client.headers.update(headers)

    async def close(self) -> None:
        """Closes the underlying HTTP client if it was created internally."""
        if self._internal_client:
            await self._client.aclose()

    async def embed(self, text: str) -> List[float]:
        """Generates a vector embedding for the given text.

        Args:
            text: The input text string.

        Returns:
            A list of floats representing the embedding vector.
        """
        payload = {
            "model": self.model,
            "input": text,
        }

        response = await self._client.post(f"{self.base_url}/embeddings", json=payload)
        response.raise_for_status()

        data = response.json()
        embedding = data["data"][0]["embedding"]
        return cast(List[float], embedding)
