"""Conversation handler for managing multi-turn slide generation conversations."""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml

from slidegen.llm.client import LLMClient
from slidegen.llm.models import LLMResponse
from slidegen.llm.prompts.builder import build_prompt, build_refinement_prompt
from slidegen.validator import ValidationResult, validate


class ConversationState(Enum):
    """State of the conversation."""

    INITIAL = "initial"  # Starting state, no schema yet
    SCHEMA_GENERATED = "schema_generated"  # Schema generated, awaiting user feedback
    REFINING = "refining"  # Refining schema based on feedback
    AMBIGUITY_RESOLUTION = "ambiguity_resolution"  # Asking user for clarification
    COMPLETE = "complete"  # Conversation complete, schema finalized


@dataclass
class ConversationMessage:
    """A message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchemaVersion:
    """A version of the schema with metadata."""

    version: int
    schema: Dict[str, Any]
    generated_at: float
    validation_result: Optional[ValidationResult] = None
    llm_response: Optional[LLMResponse] = None
    user_feedback: Optional[str] = None


class ConversationHandler:
    """
    Handles multi-turn conversations for slide generation.
    
    Manages:
    - Conversation history and context
    - Schema versioning across turns
    - Ambiguity resolution
    - Preview generation
    - Validation and refinement
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        max_history_messages: int = 20,
        max_schema_versions: int = 10,
    ):
        """
        Initialize conversation handler.
        
        Args:
            llm_client: LLM client instance (creates default if None)
            max_history_messages: Maximum number of messages to keep in history
            max_schema_versions: Maximum number of schema versions to track
        """
        self.llm_client = llm_client or LLMClient()
        self.max_history_messages = max_history_messages
        self.max_schema_versions = max_schema_versions
        
        self.state = ConversationState.INITIAL
        self.messages: List[ConversationMessage] = []
        self.schema_versions: List[SchemaVersion] = []
        self.current_schema: Optional[Dict[str, Any]] = None
        self.ambiguity_questions: List[str] = []

    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a user message to the conversation.
        
        Args:
            content: User message content
            metadata: Optional metadata (e.g., file uploads, preferences)
        """
        message = ConversationMessage(
            role="user",
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self._prune_history()

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an assistant message to the conversation.
        
        Args:
            content: Assistant message content
            metadata: Optional metadata (e.g., schema version, validation status)
        """
        message = ConversationMessage(
            role="assistant",
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self._prune_history()

    def generate_schema(
        self,
        user_prompt: Optional[str] = None,
        retry_with_validation: bool = True,
        max_retries: int = 3,
    ) -> SchemaVersion:
        """
        Generate a schema from the current conversation context.
        
        Args:
            user_prompt: Optional explicit user prompt (uses last user message if None)
            retry_with_validation: Whether to retry with validation error feedback
            max_retries: Maximum number of retry attempts
            
        Returns:
            SchemaVersion with generated schema
            
        Raises:
            RuntimeError: If schema generation fails after all retries
        """
        # Get user prompt
        if user_prompt is None:
            # Find last user message
            user_messages = [m for m in self.messages if m.role == "user"]
            if not user_messages:
                raise ValueError("No user message found. Provide user_prompt or add user message first.")
            user_prompt = user_messages[-1].content

        # Build context from conversation history
        context = self._build_context()
        
        # Generate schema
        last_error = None
        for attempt in range(max_retries):
            try:
                # Build prompt with context
                messages = build_prompt(
                    user_request=user_prompt,
                    include_examples=True,
                    max_examples=3,
                    context=context,
                )
                
                # Call LLM (convert messages to single prompt for LLMClient)
                system_prompt = messages[0]["content"] if messages else ""
                user_message = "\n".join(
                    f"{m['role']}: {m['content']}" 
                    for m in messages[1:] 
                    if m["role"] == "user"
                )
                if not user_message:
                    user_message = user_prompt
                
                llm_response = self.llm_client.generate_schema(
                    user_prompt=user_message,
                    max_retries=1,  # We handle retries here
                    retry_with_feedback=False,  # We handle feedback here
                )
                
                # Parse schema from response
                schema_dict = self._parse_schema_from_response(llm_response.content)
                
                # Validate schema
                validation_result = validate(schema_dict)
                
                # If invalid and retry enabled, retry with error feedback
                if not validation_result.is_valid and retry_with_validation and attempt < max_retries - 1:
                    error_messages = [
                        f"{err.get('field', 'unknown')}: {err.get('message', 'validation error')}"
                        for err in validation_result.errors
                    ]
                    user_prompt = f"{user_prompt}\n\nPrevious attempt had validation errors:\n" + "\n".join(f"- {e}" for e in error_messages)
                    last_error = ValueError(f"Validation failed: {len(validation_result.errors)} errors")
                    continue
                
                # Create schema version
                version = SchemaVersion(
                    version=len(self.schema_versions) + 1,
                    schema=schema_dict,
                    generated_at=__import__("time").time(),
                    validation_result=validation_result,
                    llm_response=llm_response,
                )
                
                self.schema_versions.append(version)
                self.current_schema = schema_dict
                self.state = ConversationState.SCHEMA_GENERATED
                
                # Prune old versions
                if len(self.schema_versions) > self.max_schema_versions:
                    self.schema_versions = self.schema_versions[-self.max_schema_versions:]
                
                return version
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue
                raise RuntimeError(f"Failed to generate schema after {max_retries} attempts: {last_error}") from last_error
        
        raise RuntimeError(f"Failed to generate schema after {max_retries} attempts: {last_error}")

    def refine_schema(
        self,
        user_feedback: str,
        max_retries: int = 3,
    ) -> SchemaVersion:
        """
        Refine the current schema based on user feedback.
        
        Args:
            user_feedback: User's feedback on the current schema
            max_retries: Maximum number of retry attempts
            
        Returns:
            New SchemaVersion with refined schema
            
        Raises:
            ValueError: If no current schema exists
            RuntimeError: If refinement fails after all retries
        """
        if self.current_schema is None:
            raise ValueError("No current schema to refine. Generate a schema first.")
        
        # Add user feedback message
        self.add_user_message(user_feedback, metadata={"type": "refinement"})
        
        # Get original request from conversation
        original_request = self._get_original_request()
        
        # Build refinement prompt
        schema_yaml = yaml.dump(self.current_schema, default_flow_style=False)
        validation_errors = []
        if self.schema_versions:
            last_version = self.schema_versions[-1]
            if last_version.validation_result and not last_version.validation_result.is_valid:
                validation_errors = [
                    f"{err.get('field', 'unknown')}: {err.get('message', 'error')}"
                    for err in last_version.validation_result.errors
                ]
        
        messages = build_refinement_prompt(
            original_request=original_request,
            generated_schema=schema_yaml,
            validation_errors=validation_errors,
            user_feedback=user_feedback,
        )
        
        # Call LLM
        system_prompt = messages[0]["content"]
        user_message = "\n".join(m["content"] for m in messages[1:] if m["role"] == "user")
        
        last_error = None
        for attempt in range(max_retries):
            try:
                llm_response = self.llm_client.generate_schema(
                    user_prompt=user_message,
                    max_retries=1,
                    retry_with_feedback=False,
                )
                
                # Parse schema
                schema_dict = self._parse_schema_from_response(llm_response.content)
                
                # Validate
                validation_result = validate(schema_dict)
                
                # Create new version
                version = SchemaVersion(
                    version=len(self.schema_versions) + 1,
                    schema=schema_dict,
                    generated_at=__import__("time").time(),
                    validation_result=validation_result,
                    llm_response=llm_response,
                    user_feedback=user_feedback,
                )
                
                self.schema_versions.append(version)
                self.current_schema = schema_dict
                self.state = ConversationState.REFINING
                
                # Prune old versions
                if len(self.schema_versions) > self.max_schema_versions:
                    self.schema_versions = self.schema_versions[-self.max_schema_versions:]
                
                return version
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue
                raise RuntimeError(f"Failed to refine schema after {max_retries} attempts: {last_error}") from last_error
        
        raise RuntimeError(f"Failed to refine schema after {max_retries} attempts: {last_error}")

    def check_ambiguity(self, user_prompt: str) -> List[str]:
        """
        Check if user prompt has ambiguities that need clarification.
        
        Args:
            user_prompt: User's prompt to check
            
        Returns:
            List of clarification questions (empty if no ambiguities)
        """
        # Simple ambiguity detection
        questions = []
        
        # Check for vague requests
        vague_indicators = ["slides", "presentation", "deck"]
        if any(indicator in user_prompt.lower() for indicator in vague_indicators):
            # Check if specific details are missing
            if "how many" not in user_prompt.lower() and "number" not in user_prompt.lower():
                if len([s for s in user_prompt.split() if s.lower() in ["1", "2", "3", "4", "5", "one", "two", "three", "four", "five"]]) == 0:
                    questions.append("How many slides would you like?")
            
            if "topic" not in user_prompt.lower() and "about" not in user_prompt.lower():
                questions.append("What topic or theme should the presentation cover?")
        
        # Check for missing chart/table data
        if "chart" in user_prompt.lower() or "graph" in user_prompt.lower():
            if "data" not in user_prompt.lower() and "numbers" not in user_prompt.lower():
                questions.append("Do you have data for the chart, or should I generate sample data?")
        
        self.ambiguity_questions = questions
        if questions:
            self.state = ConversationState.AMBIGUITY_RESOLUTION
        
        return questions

    def generate_preview(self, schema: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a text preview of the schema.
        
        Args:
            schema: Schema to preview (uses current_schema if None)
            
        Returns:
            Text preview of the presentation
        """
        if schema is None:
            schema = self.current_schema
        
        if schema is None:
            return "No schema available to preview."
        
        presentation = schema.get("presentation", {})
        title = presentation.get("title", "Untitled Presentation")
        slides = presentation.get("slides", [])
        
        preview_lines = [f"Preview: {title}", ""]
        
        for idx, slide in enumerate(slides, 1):
            layout = slide.get("layout", "unknown")
            preview_lines.append(f"Slide {idx}: [{layout}]")
            
            if layout == "title":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                if "subtitle" in slide:
                    preview_lines.append(f"  - Subtitle: {slide.get('subtitle')}")
            
            elif layout == "section_header":
                preview_lines.append(f"  - Text: {slide.get('text', 'N/A')}")
            
            elif layout == "bullet_list":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                bullets = slide.get("bullets", [])
                bullet_count = len(bullets)
                preview_lines.append(f"  - {bullet_count} bullets")
                # Show first 3 bullets
                for bullet in bullets[:3]:
                    if isinstance(bullet, str):
                        preview_lines.append(f"    • {bullet[:60]}...")
                    elif isinstance(bullet, dict):
                        text = bullet.get("text", "")
                        preview_lines.append(f"    • {text[:60]}...")
                if bullet_count > 3:
                    preview_lines.append(f"    ... and {bullet_count - 3} more")
            
            elif layout == "two_column":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                preview_lines.append("  - Two columns with content")
            
            elif layout == "comparison":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                preview_lines.append("  - Before/After comparison")
            
            elif layout == "chart":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                chart = slide.get("chart", {})
                chart_type = chart.get("type", "unknown")
                preview_lines.append(f"  - Chart type: {chart_type}")
            
            elif layout == "table":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                table = slide.get("table", {})
                data = table.get("data", [])
                preview_lines.append(f"  - Table with {len(data)} rows")
            
            elif layout == "quote":
                quote = slide.get("quote", {})
                text = quote.get("text", "N/A")
                preview_lines.append(f"  - Quote: {text[:60]}...")
                if "attribution" in quote:
                    preview_lines.append(f"  - Attribution: {quote.get('attribution')}")
            
            elif layout == "image":
                preview_lines.append(f"  - Title: {slide.get('title', 'N/A')}")
                image = slide.get("image", {})
                preview_lines.append(f"  - Image: {image.get('src', 'N/A')}")
            
            elif layout == "blank":
                preview_lines.append("  - Blank slide")
            
            preview_lines.append("")
        
        return "\n".join(preview_lines)

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the conversation state.
        
        Returns:
            Dictionary with conversation summary
        """
        return {
            "state": self.state.value,
            "message_count": len(self.messages),
            "schema_version_count": len(self.schema_versions),
            "current_schema_valid": (
                self.schema_versions[-1].validation_result.is_valid
                if self.schema_versions and self.schema_versions[-1].validation_result
                else None
            ),
            "has_ambiguities": len(self.ambiguity_questions) > 0,
            "ambiguity_questions": self.ambiguity_questions,
        }

    def _build_context(self) -> str:
        """Build context string from conversation history."""
        if not self.messages:
            return ""
        
        # Get recent messages (last 10)
        recent_messages = self.messages[-10:]
        
        context_parts = ["## Conversation History\n"]
        for msg in recent_messages:
            role = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role}: {msg.content[:200]}...")
        
        # Add schema version info if available
        if self.schema_versions:
            last_version = self.schema_versions[-1]
            context_parts.append(f"\n## Previous Schema (Version {last_version.version})")
            if last_version.validation_result and not last_version.validation_result.is_valid:
                errors = [
                    f"- {err.get('field', 'unknown')}: {err.get('message', 'error')}"
                    for err in last_version.validation_result.errors[:3]
                ]
                context_parts.append("Previous schema had validation errors:")
                context_parts.extend(errors)
        
        return "\n".join(context_parts)

    def _get_original_request(self) -> str:
        """Get the original user request from conversation history."""
        user_messages = [m for m in self.messages if m.role == "user"]
        if user_messages:
            return user_messages[0].content
        return "Generate a presentation"

    def _parse_schema_from_response(self, content: str) -> Dict[str, Any]:
        """
        Parse schema from LLM response content.
        
        Args:
            content: LLM response content (may be JSON or YAML)
            
        Returns:
            Parsed schema dictionary
        """
        # Try JSON first
        try:
            # Remove markdown code fences if present
            content_clean = content.strip()
            if content_clean.startswith("```"):
                # Extract content between code fences
                lines = content_clean.split("\n")
                content_clean = "\n".join(
                    line for line in lines[1:-1] 
                    if not line.strip().startswith("```")
                )
            
            # Try JSON
            return json.loads(content_clean)
        except json.JSONDecodeError:
            pass
        
        # Try YAML
        try:
            return yaml.safe_load(content_clean)
        except yaml.YAMLError:
            pass
        
        # If both fail, try to extract JSON object from text
        import re
        json_match = re.search(r'\{.*\}', content_clean, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not parse schema from response: {content[:200]}...")

    def _prune_history(self) -> None:
        """Prune conversation history to keep within limits."""
        if len(self.messages) > self.max_history_messages:
            # Keep first message (original request) and recent messages
            if len(self.messages) > 1:
                first_message = self.messages[0]
                recent_messages = self.messages[-(self.max_history_messages - 1):]
                self.messages = [first_message] + recent_messages
            else:
                self.messages = self.messages[-self.max_history_messages:]

