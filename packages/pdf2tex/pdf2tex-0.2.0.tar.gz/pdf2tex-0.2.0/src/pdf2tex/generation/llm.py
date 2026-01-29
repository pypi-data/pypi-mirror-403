"""
LLM client using Hugging Face Inference API.

Provides access to various LLMs for LaTeX generation.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    finish_reason: str | None
    usage: dict[str, int] | None
    metadata: dict[str, Any]


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    max_tokens: int = 4096
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    stop_sequences: list[str] | None = None


class LLMClient:
    """
    Client for Hugging Face Inference API.
    
    Supports multiple models with automatic fallback:
    - Llama 3.1 70B (primary)
    - Mixtral 8x7B (fallback)
    - DeepSeek-Math (math-specialized)
    """

    DEFAULT_MODELS = [
        "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "deepseek-ai/deepseek-math-7b-instruct",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        fallback_models: list[str] | None = None,
        api_url: str = "https://api-inference.huggingface.co/models",
        timeout: int = 120,
    ) -> None:
        """
        Initialize LLM client.

        Args:
            api_key: HuggingFace API key
            model_name: Primary model name
            fallback_models: List of fallback models
            api_url: HuggingFace API URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model_name = model_name or self.DEFAULT_MODELS[0]
        self.fallback_models = fallback_models or self.DEFAULT_MODELS[1:]
        self.api_url = api_url
        self.timeout = timeout

        self._client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._initialized:
            return

        try:
            import httpx

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            self._initialized = True
            logger.info("LLM client initialized", model=self.model_name)

        except Exception as e:
            logger.error("Failed to initialize LLM client", error=str(e))
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        config: GenerationConfig | None = None,
    ) -> LLMResponse:
        """
        Generate text from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration

        Returns:
            LLM response
        """
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        models_to_try = [self.model_name] + self.fallback_models

        last_error: Exception | None = None

        for model in models_to_try:
            try:
                response = await self._generate_with_model(
                    model, prompt, system_prompt, config
                )
                return response
            except Exception as e:
                logger.warning(
                    "Model generation failed, trying fallback",
                    model=model,
                    error=str(e),
                )
                last_error = e
                continue

        raise RuntimeError(
            f"All models failed. Last error: {last_error}"
        )

    async def _generate_with_model(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None,
        config: GenerationConfig,
    ) -> LLMResponse:
        """Generate with specific model."""
        url = f"{self.api_url}/{model}"

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request
        payload = {
            "inputs": self._format_messages(messages, model),
            "parameters": {
                "max_new_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "repetition_penalty": config.repetition_penalty,
                "return_full_text": False,
            },
        }

        if config.stop_sequences:
            payload["parameters"]["stop"] = config.stop_sequences

        # Make request
        response = await self._client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()

        # Parse response
        if isinstance(data, list) and len(data) > 0:
            generated_text = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            generated_text = data.get("generated_text", "")
        else:
            generated_text = str(data)

        return LLMResponse(
            content=generated_text.strip(),
            model=model,
            finish_reason="stop",
            usage=None,
            metadata={"raw_response": data},
        )

    def _format_messages(
        self,
        messages: list[dict[str, str]],
        model: str,
    ) -> str:
        """Format messages for specific model."""
        # Llama 3 format
        if "llama" in model.lower():
            formatted = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    formatted += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
                elif role == "user":
                    formatted += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
                elif role == "assistant":
                    formatted += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
            formatted += "<|start_header_id|>assistant<|end_header_id|>\n\n"
            return formatted

        # Mixtral/Mistral format
        if "mistral" in model.lower() or "mixtral" in model.lower():
            formatted = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    formatted += f"[INST] {content} [/INST]"
                elif role == "user":
                    formatted += f"[INST] {content} [/INST]"
                elif role == "assistant":
                    formatted += f" {content}</s>"
            return formatted

        # Default: simple concatenation
        parts = []
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            parts.append(f"{role}: {content}")
        return "\n".join(parts) + "\nASSISTANT:"

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream generated text.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration

        Yields:
            Generated text chunks
        """
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        url = f"{self.api_url}/{self.model_name}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "inputs": self._format_messages(messages, self.model_name),
            "parameters": {
                "max_new_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "return_full_text": False,
            },
            "stream": True,
        }

        async with self._client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    import json
                    try:
                        data = json.loads(line[5:])
                        if "token" in data:
                            yield data["token"]["text"]
                    except json.JSONDecodeError:
                        continue

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> LLMResponse:
        """
        Generate from chat messages.

        Args:
            messages: List of messages with role and content
            config: Generation configuration

        Returns:
            LLM response
        """
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()

        # Extract system and user messages
        system_prompt = None
        prompt = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                prompt = msg["content"]

        return await self.generate(prompt, system_prompt, config)

    def get_info(self) -> dict[str, Any]:
        """Get client information."""
        return {
            "model_name": self.model_name,
            "fallback_models": self.fallback_models,
            "api_url": self.api_url,
            "timeout": self.timeout,
            "initialized": self._initialized,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False


class MathLLMClient(LLMClient):
    """
    LLM client specialized for mathematical content.
    
    Uses DeepSeek-Math for math-heavy content.
    """

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize with math-specialized model."""
        kwargs.setdefault("model_name", "deepseek-ai/deepseek-math-7b-instruct")
        super().__init__(**kwargs)

    async def generate_math(
        self,
        math_content: str,
        context: str | None = None,
    ) -> LLMResponse:
        """
        Generate LaTeX for mathematical content.

        Args:
            math_content: Math expression or equation
            context: Optional context

        Returns:
            LLM response with LaTeX
        """
        system_prompt = """You are a mathematical typesetting expert. 
Convert the given mathematical content to precise LaTeX code.
Ensure all symbols, operators, and formatting are correct.
Use standard LaTeX math environments (equation, align, etc.)."""

        prompt = f"Convert to LaTeX:\n{math_content}"
        if context:
            prompt = f"Context: {context}\n\n{prompt}"

        config = GenerationConfig(
            temperature=0.1,  # Low temperature for precision
            max_tokens=2048,
        )

        return await self.generate(prompt, system_prompt, config)
