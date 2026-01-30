"""Prompt engineering for LLM schema generation."""

from slidegen.llm.prompts.builder import build_prompt, build_refinement_prompt
from slidegen.llm.prompts.examples import get_few_shot_examples, get_examples_by_layout
from slidegen.llm.prompts.system import get_system_prompt

__all__ = [
    "get_system_prompt",
    "get_few_shot_examples",
    "get_examples_by_layout",
    "build_prompt",
    "build_refinement_prompt",
]

