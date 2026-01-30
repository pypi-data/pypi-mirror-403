"""Error message formatting for validation errors."""

from typing import Any, Dict, List, Optional


def format_error_message(error: Dict[str, Any], slide_num: Optional[int] = None) -> str:
    """
    Format a validation error into a human-readable message.
    
    Args:
        error: Error dictionary with message, field, suggestion, etc.
        slide_num: Optional slide number for context
        
    Returns:
        Formatted error message string
    """
    parts = []
    
    # Add slide context if available
    if slide_num:
        parts.append(f"Slide {slide_num}:")
    elif "slide" in error:
        parts.append(f"Slide {error['slide']}:")
    
    # Add field context
    field = error.get("field", "unknown")
    if field and field != "unknown":
        parts.append(f"Field '{field}':")
    
    # Add error message
    message = error.get("message", "Validation error")
    parts.append(message)
    
    # Add suggestion if available
    suggestion = error.get("suggestion")
    if suggestion:
        parts.append(f"\n  → Suggestion: {suggestion}")
    
    return " ".join(parts)


def format_validation_result(result, file_path: Optional[str] = None) -> str:
    """
    Format a ValidationResult into a complete report.
    
    Args:
        result: ValidationResult object
        file_path: Optional file path for context
        
    Returns:
        Formatted report string
    """
    lines = []
    
    if file_path:
        lines.append(f"Validating: {file_path}")
        lines.append("")
    
    if result.is_valid:
        lines.append("✓ Schema is valid")
        
        if result.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in result.warnings:
                lines.append(f"  ⚠ {warning}")
    else:
        lines.append("✗ Validation failed")
        lines.append("")
        lines.append(f"Found {len(result.errors)} error(s):")
        lines.append("")
        
        for idx, error in enumerate(result.errors, 1):
            lines.append(f"{idx}. {format_error_message(error)}")
            lines.append("")
    
    return "\n".join(lines)

