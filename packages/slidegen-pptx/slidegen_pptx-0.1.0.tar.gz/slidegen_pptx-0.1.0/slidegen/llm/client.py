"""LLM client with OpenAI and DeepSeek integration."""

import os
from typing import Any, Dict, List, Optional

from slidegen.llm.models import CostEstimate, LLMResponse, TokenUsage
from slidegen.llm.prompts.builder import build_prompt


class LLMClient:
    """
    Client for interacting with LLM providers (OpenAI, DeepSeek).
    
    Supports fallback logic and retry with error feedback.
    """

    # Pricing per 1M tokens (as of 2025-01)
    PRICING = {
        "openai": {
            "gpt-4o-mini": {
                "input": 0.075,
                "output": 0.30,
            }
        },
        "deepseek": {
            "deepseek-chat": {
                "input": 0.27,
                "output": 1.10,
            }
        },
    }

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        default_provider: str = "openai",
    ):
        """
        Initialize LLM client.
        
        Args:
            openai_api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            deepseek_api_key: DeepSeek API key (or use DEEPSEEK_API_KEY env var)
            default_provider: Default provider to use ("openai" or "deepseek")
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.default_provider = default_provider
        self._openai_client = None
        self._deepseek_client = None

    def _get_openai_client(self):
        """Get or create OpenAI client."""
        if self._openai_client is None:
            try:
                from openai import OpenAI

                if not self.openai_api_key:
                    raise ValueError("OpenAI API key not provided")
                self._openai_client = OpenAI(api_key=self.openai_api_key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )
        return self._openai_client

    def _get_deepseek_client(self):
        """Get or create DeepSeek client."""
        if self._deepseek_client is None:
            try:
                from openai import OpenAI

                if not self.deepseek_api_key:
                    raise ValueError("DeepSeek API key not provided")
                # DeepSeek uses OpenAI-compatible API
                self._deepseek_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com",
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )
        return self._deepseek_client

    def generate_schema(
        self,
        user_prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_with_feedback: bool = True,
    ) -> LLMResponse:
        """
        Generate a slide schema from a user prompt.
        
        Args:
            user_prompt: Natural language description of desired presentation
            provider: Provider to use ("openai" or "deepseek"), defaults to default_provider
            model: Model to use, defaults to provider's default model
            max_retries: Maximum number of retry attempts
            retry_with_feedback: Whether to retry with validation error feedback
            
        Returns:
            LLMResponse with generated schema
            
        Raises:
            ValueError: If provider/model not supported or API key missing
            RuntimeError: If all retry attempts fail
        """
        provider = provider or self.default_provider

        # Set default models
        if model is None:
            if provider == "openai":
                model = "gpt-4o-mini"
            elif provider == "deepseek":
                model = "deepseek-chat"
            else:
                raise ValueError(f"Unknown provider: {provider}")

        # Build prompt
        from slidegen.llm.prompts.system import get_system_prompt
        from slidegen.llm.prompts.examples import get_few_shot_examples
        
        system_prompt = get_system_prompt()
        # Add few-shot examples to system prompt
        examples = get_few_shot_examples()[:3]  # Use 3 examples
        if examples:
            example_text = "\n\n## Examples\n\n"
            for ex in examples:
                example_text += f"User: {ex['user']}\n\nAssistant: {ex['assistant']}\n\n---\n\n"
            system_prompt += example_text
        user_message = user_prompt

        # Try with fallback
        last_error = None
        for attempt in range(max_retries):
            try:
                # Try primary provider
                response = self._call_provider(
                    provider=provider,
                    model=model,
                    system_prompt=system_prompt,
                    user_message=user_message,
                )

                # Validate response (basic check - full validation happens elsewhere)
                if response.content.strip():
                    return response

                # If empty response, retry
                last_error = ValueError("Empty response from LLM")

            except Exception as e:
                last_error = e
                # Try fallback provider if not last attempt
                if attempt < max_retries - 1:
                    if provider == "openai":
                        provider = "deepseek"
                        model = "deepseek-chat"
                    else:
                        provider = "openai"
                        model = "gpt-4o-mini"

                    # If retry_with_feedback and we have validation errors, include them
                    if retry_with_feedback and isinstance(e, ValueError):
                        user_message = f"{user_message}\n\nPrevious attempt failed: {str(e)}. Please fix the schema."

        raise RuntimeError(
            f"Failed to generate schema after {max_retries} attempts: {last_error}"
        )

    def _call_provider(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        """
        Call a specific LLM provider.
        
        Args:
            provider: Provider name ("openai" or "deepseek")
            model: Model name
            system_prompt: System prompt
            user_message: User message
            
        Returns:
            LLMResponse with generated content
        """
        if provider == "openai":
            return self._call_openai(model, system_prompt, user_message)
        elif provider == "deepseek":
            return self._call_deepseek(model, system_prompt, user_message)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _call_openai(
        self, model: str, system_prompt: str, user_message: str
    ) -> LLMResponse:
        """Call OpenAI API."""
        client = self._get_openai_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},  # Request structured output
        )

        # Extract token usage
        usage = response.usage
        token_usage = TokenUsage(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

        # Calculate cost
        pricing = self.PRICING["openai"][model]
        cost_estimate = CostEstimate(
            provider="openai",
            model=model,
            input_cost=pricing["input"],
            output_cost=pricing["output"],
            estimated_cost=(
                (usage.prompt_tokens / 1_000_000) * pricing["input"]
                + (usage.completion_tokens / 1_000_000) * pricing["output"]
            ),
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            provider="openai",
            model=model,
            token_usage=token_usage,
            cost_estimate=cost_estimate,
            raw_response=response,
        )

    def _call_deepseek(
        self, model: str, system_prompt: str, user_message: str
    ) -> LLMResponse:
        """Call DeepSeek API."""
        client = self._get_deepseek_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        # Extract token usage
        usage = response.usage
        token_usage = TokenUsage(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

        # Calculate cost
        pricing = self.PRICING["deepseek"][model]
        cost_estimate = CostEstimate(
            provider="deepseek",
            model=model,
            input_cost=pricing["input"],
            output_cost=pricing["output"],
            estimated_cost=(
                (usage.prompt_tokens / 1_000_000) * pricing["input"]
                + (usage.completion_tokens / 1_000_000) * pricing["output"]
            ),
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            provider="deepseek",
            model=model,
            token_usage=token_usage,
            cost_estimate=cost_estimate,
            raw_response=response,
        )

