"""Core validation logic for SlideGen schemas."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema import ValidationError

from slidegen.validator.messages import format_error_message


class ValidationResult:
    """Result of schema validation."""

    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:
        status = "valid" if self.is_valid else "invalid"
        error_count = len(self.errors)
        return f"ValidationResult({status}, {error_count} errors)"


def _load_schema() -> Dict[str, Any]:
    """Load the JSON Schema specification."""
    schema_path = Path(__file__).parent.parent.parent / "schema" / "spec" / "slide-schema.json"
    
    # If schema not in worktree, try main directory
    if not schema_path.exists():
        schema_path = Path(__file__).parent.parent.parent.parent / "schema" / "spec" / "slide-schema.json"
    
    if not schema_path.exists():
        # Fallback: try to find it relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        schema_path = project_root / ".trees" / "task-001-schema" / "schema" / "spec" / "slide-schema.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found. Expected at: {schema_path}. "
            "Ensure schema/spec/slide-schema.json exists."
        )
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_business_rules(schema_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply custom business logic validators."""
    errors = []
    
    presentation = schema_data.get("presentation", {})
    slides = presentation.get("slides", [])
    
    # Validate each slide
    for idx, slide in enumerate(slides):
        slide_num = idx + 1
        
        # Check bullet limits
        if slide.get("layout") == "bullet_list":
            bullets = slide.get("bullets", [])
            if len(bullets) > 10:
                errors.append({
                    "slide": slide_num,
                    "field": "bullets",
                    "message": f"Too many bullets ({len(bullets)}). Maximum is 10 per slide.",
                    "suggestion": "Split into multiple slides or reduce bullet count.",
                })
        
        # Check chart data format
        if slide.get("layout") == "chart":
            chart = slide.get("chart", {})
            data = chart.get("data", {})
            
            if isinstance(data, dict) and "labels" in data and "values" in data:
                labels = data.get("labels", [])
                values = data.get("values", [])
                
                if len(labels) != len(values):
                    errors.append({
                        "slide": slide_num,
                        "field": "chart.data",
                        "message": f"Chart data mismatch: {len(labels)} labels but {len(values)} values.",
                        "suggestion": "Ensure labels and values arrays have the same length.",
                    })
        
        # Check table data
        if slide.get("layout") == "table":
            table = slide.get("table", {})
            table_data = table.get("data", [])
            
            if isinstance(table_data, list) and len(table_data) > 0:
                # Check all rows have same length
                first_row_len = len(table_data[0]) if table_data else 0
                for row_idx, row in enumerate(table_data[1:], start=2):
                    if len(row) != first_row_len:
                        errors.append({
                            "slide": slide_num,
                            "field": f"table.data[row {row_idx}]",
                            "message": f"Table row {row_idx} has {len(row)} columns, expected {first_row_len}.",
                            "suggestion": "Ensure all table rows have the same number of columns.",
                        })
    
    return errors


def validate(schema_data: Dict[str, Any], schema_path: Optional[Path] = None) -> ValidationResult:
    """
    Validate a schema dictionary against the SlideGen schema specification.
    
    Args:
        schema_data: The schema dictionary to validate
        schema_path: Optional path to schema file (for better error messages)
        
    Returns:
        ValidationResult with validation status and any errors
    """
    errors = []
    warnings = []
    
    # Load JSON Schema
    try:
        json_schema = _load_schema()
    except FileNotFoundError as e:
        return ValidationResult(
            is_valid=False,
            errors=[{
                "message": str(e),
                "field": "schema",
                "suggestion": "Ensure schema/spec/slide-schema.json exists in the project.",
            }],
        )
    
    # Validate against JSON Schema
    try:
        jsonschema.validate(instance=schema_data, schema=json_schema)
    except ValidationError as e:
        # Format JSON Schema errors
        error_path = " -> ".join(str(p) for p in e.absolute_path)
        field_name = error_path if error_path else e.json_path
        
        errors.append({
            "message": e.message,
            "field": field_name,
            "json_path": str(e.json_path),
            "suggestion": _suggest_fix(e),
        })
    
    # Apply business logic validators
    business_errors = _validate_business_rules(schema_data)
    errors.extend(business_errors)
    
    # Check for common issues (warnings)
    presentation = schema_data.get("presentation", {})
    slides = presentation.get("slides", [])
    
    if len(slides) == 0:
        warnings.append("Presentation has no slides. Add at least one slide.")
    elif len(slides) > 100:
        warnings.append(f"Large presentation ({len(slides)} slides). Consider splitting into multiple files.")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _suggest_fix(error: ValidationError) -> str:
    """Generate a suggestion for fixing a validation error."""
    error_msg = error.message.lower()
    
    if "required" in error_msg:
        missing_field = error.absolute_path[-1] if error.absolute_path else "field"
        return f"Add the required '{missing_field}' field."
    
    if "enum" in error_msg or "not one of" in error_msg:
        return "Check the allowed values for this field in the schema documentation."
    
    if "type" in error_msg:
        expected_type = error_msg.split("'")[1] if "'" in error_msg else "correct type"
        return f"Ensure this field is of type {expected_type}."
    
    if "format" in error_msg:
        return "Check the format requirements for this field (e.g., hex color codes must be #RRGGBB)."
    
    return "Refer to the schema documentation for the correct format."


def validate_file(file_path: Path) -> ValidationResult:
    """
    Validate a schema file (YAML or JSON).
    
    Args:
        file_path: Path to the schema file
        
    Returns:
        ValidationResult with validation status and any errors
    """
    import yaml
    
    if not file_path.exists():
        return ValidationResult(
            is_valid=False,
            errors=[{
                "message": f"File not found: {file_path}",
                "field": "file_path",
                "suggestion": "Check that the file path is correct.",
            }],
        )
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix in [".yaml", ".yml"]:
                schema_data = yaml.safe_load(f)
            elif file_path.suffix == ".json":
                schema_data = json.load(f)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[{
                        "message": f"Unsupported file format: {file_path.suffix}",
                        "field": "file_path",
                        "suggestion": "Use .yaml, .yml, or .json file extension.",
                    }],
                )
    except yaml.YAMLError as e:
        return ValidationResult(
            is_valid=False,
            errors=[{
                "message": f"YAML parsing error: {str(e)}",
                "field": "file_path",
                "suggestion": "Check YAML syntax. Common issues: missing quotes, incorrect indentation.",
            }],
        )
    except json.JSONDecodeError as e:
        return ValidationResult(
            is_valid=False,
            errors=[{
                "message": f"JSON parsing error: {str(e)}",
                "field": "file_path",
                "suggestion": "Check JSON syntax. Ensure proper comma placement and quote usage.",
            }],
        )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[{
                "message": f"Error reading file: {str(e)}",
                "field": "file_path",
                "suggestion": "Ensure the file is readable and not corrupted.",
            }],
        )
    
    return validate(schema_data, schema_path=file_path)

