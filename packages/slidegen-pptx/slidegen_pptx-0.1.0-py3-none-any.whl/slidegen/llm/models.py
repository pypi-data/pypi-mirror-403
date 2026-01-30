"""Data models for LLM integration."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TokenUsage:
    """Token usage information for an LLM request."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class CostEstimate:
    """Cost estimate for an LLM request."""

    provider: str
    model: str
    input_cost: float  # Cost per 1M input tokens
    output_cost: float  # Cost per 1M output tokens
    estimated_cost: float  # Estimated cost for this request

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "model": self.model,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "estimated_cost": self.estimated_cost,
        }


@dataclass
class LLMResponse:
    """Response from an LLM request."""

    content: str
    provider: str
    model: str
    token_usage: TokenUsage
    cost_estimate: Optional[CostEstimate] = None
    raw_response: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "token_usage": self.token_usage.to_dict(),
        }
        if self.cost_estimate:
            result["cost_estimate"] = self.cost_estimate.to_dict()
        return result

