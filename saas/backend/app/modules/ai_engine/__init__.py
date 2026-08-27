"""AI Provider abstraction — supports OpenAI, Anthropic, Google, and custom providers."""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("mailpilot.ai")


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: str = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: list[dict] = None,
    ) -> dict:
        """
        Send a chat completion request.
        Returns: {"content": str, "tool_calls": list, "usage": dict, "model": str}
        """
        pass

    @abstractmethod
    async def embed(self, texts: list[str], model: str = None) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    async def chat(self, messages, model=None, system_prompt=None, temperature=0.7, max_tokens=2000, tools=None):
        import httpx
        model = model or "gpt-4o-mini"
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        payload = {"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=30,
            )
            data = resp.json()
            if "error" in data:
                raise Exception(data["error"].get("message", "OpenAI error"))

            choice = data["choices"][0]
            return {
                "content": choice["message"].get("content", ""),
                "tool_calls": choice["message"].get("tool_calls", []),
                "usage": data.get("usage", {}),
                "model": data.get("model", model),
            }

    async def embed(self, texts, model=None):
        import httpx
        model = model or "text-embedding-3-small"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                json={"input": texts, "model": model},
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=30,
            )
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    async def chat(self, messages, model=None, system_prompt=None, temperature=0.7, max_tokens=2000, tools=None):
        import httpx
        model = model or "claude-sonnet-4-20250514"

        payload = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "messages": messages}
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            data = resp.json()
            if "error" in data:
                raise Exception(data["error"].get("message", "Anthropic error"))

            content = ""
            tool_calls = []
            for block in data.get("content", []):
                if block["type"] == "text":
                    content += block["text"]
                elif block["type"] == "tool_use":
                    tool_calls.append({"id": block["id"], "function": {"name": block["name"], "arguments": json.dumps(block["input"])}})

            return {"content": content, "tool_calls": tool_calls, "usage": data.get("usage", {}), "model": model}

    async def embed(self, texts, model=None):
        raise NotImplementedError("Anthropic does not provide embeddings API")


class GoogleProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")

    async def chat(self, messages, model=None, system_prompt=None, temperature=0.7, max_tokens=2000, tools=None):
        import httpx
        model = model or "gemini-2.5-flash"

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
                json=payload,
                timeout=30,
            )
            data = resp.json()
            if "error" in data:
                raise Exception(data["error"].get("message", "Google AI error"))

            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"content": text, "tool_calls": [], "usage": data.get("usageMetadata", {}), "model": model}

    async def embed(self, texts, model=None):
        raise NotImplementedError("Google embeddings not yet implemented")


class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    async def chat(self, messages, model=None, system_prompt=None, temperature=0.7, max_tokens=2000, tools=None):
        import httpx
        model = model or "meta-llama/llama-3.1-8b-instruct:free"
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        payload = {"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://multi-agent-platform.local",
                    "X-Title": "Multi-Agent Platform",
                },
                timeout=30,
            )
            data = resp.json()
            if "error" in data:
                raise Exception(data["error"].get("message", "OpenRouter error"))

            choice = data["choices"][0]
            return {
                "content": choice["message"].get("content", ""),
                "tool_calls": choice["message"].get("tool_calls", []),
                "usage": data.get("usage", {}),
                "model": data.get("model", model),
            }

    async def embed(self, texts, model=None):
        raise NotImplementedError("OpenRouter does not provide embeddings API")


# ── Provider factory ──────────────────────────────────────────────
PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(name: str = None) -> AIProvider:
    name = name or os.getenv("AI_PROVIDER", "openai")
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown AI provider: {name}. Available: {list(PROVIDERS.keys())}")
    return cls()
