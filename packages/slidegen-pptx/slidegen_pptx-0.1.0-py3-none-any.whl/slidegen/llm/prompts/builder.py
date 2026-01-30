"""Prompt builder for LLM interactions."""

from typing import List, Optional

from slidegen.llm.prompts.examples import get_few_shot_examples
from slidegen.llm.prompts.system import get_system_prompt


def build_prompt(
    user_request: str,
    include_examples: bool = True,
    max_examples: int = 5,
    context: Optional[str] = None,
) -> List[dict]:
    """
    Build a complete prompt for LLM schema generation.
    
    Args:
        user_request: The user's natural language request
        include_examples: Whether to include few-shot examples
        max_examples: Maximum number of examples to include
        context: Optional additional context (e.g., previous conversation)
        
    Returns:
        List of message dictionaries for LLM API (system + examples + user)
    """
    messages = []
    
    # System prompt
    system_prompt = get_system_prompt()
    if context:
        system_prompt += f"\n\n## Additional Context\n{context}"
    
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Few-shot examples
    if include_examples:
        examples = get_few_shot_examples()[:max_examples]
        for example in examples:
            messages.append({
                "role": "user",
                "content": example["user"]
            })
            messages.append({
                "role": "assistant",
                "content": example["assistant"]
            })
    
    # User request
    messages.append({
        "role": "user",
        "content": user_request
    })
    
    return messages


def build_refinement_prompt(
    original_request: str,
    generated_schema: str,
    validation_errors: List[str],
    user_feedback: Optional[str] = None,
) -> List[dict]:
    """
    Build a prompt for refining a generated schema based on validation errors.
    
    Args:
        original_request: The original user request
        generated_schema: The schema that was generated
        validation_errors: List of validation error messages
        user_feedback: Optional user feedback
        
    Returns:
        List of message dictionaries for LLM API
    """
    messages = []
    
    # System prompt
    messages.append({
        "role": "system",
        "content": get_system_prompt() + "\n\nYou are now refining a previously generated schema that had validation errors. Fix all errors and ensure the schema is valid."
    })
    
    # Original request and response
    messages.append({
        "role": "user",
        "content": original_request
    })
    messages.append({
        "role": "assistant",
        "content": generated_schema
    })
    
    # Error feedback
    error_text = "\n".join(f"- {error}" for error in validation_errors)
    feedback = f"The generated schema has validation errors:\n\n{error_text}"
    
    if user_feedback:
        feedback += f"\n\nAdditional user feedback: {user_feedback}"
    
    feedback += "\n\nPlease generate a corrected schema that fixes all these errors."
    
    messages.append({
        "role": "user",
        "content": feedback
    })
    
    return messages

