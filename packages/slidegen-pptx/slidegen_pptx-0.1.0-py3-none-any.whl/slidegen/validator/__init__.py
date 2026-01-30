"""Schema validation module for SlideGen."""

from slidegen.validator.core import ValidationResult, validate
from slidegen.validator.messages import format_error_message

__all__ = ["validate", "ValidationResult", "format_error_message"]

