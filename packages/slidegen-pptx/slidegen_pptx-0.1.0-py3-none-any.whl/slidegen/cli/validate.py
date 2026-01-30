"""CLI command for schema validation."""

import sys
from pathlib import Path

import click

from slidegen.validator import validate_file
from slidegen.validator.messages import format_validation_result


@click.command()
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed validation output",
)
def validate_cmd(schema_file: Path, verbose: bool) -> None:
    """
    Validate a SlideGen schema file.
    
    SCHEMA_FILE: Path to the schema file (YAML or JSON) to validate
    """
    result = validate_file(schema_file)
    report = format_validation_result(result, file_path=str(schema_file))
    
    if verbose or not result.is_valid:
        click.echo(report)
    
    if not result.is_valid:
        sys.exit(1)
    
    # Show summary for valid schemas
    if result.is_valid and not verbose:
        click.echo("✓ Schema is valid")
        
        # Count slides if possible
        try:
            import yaml
            with open(schema_file, "r", encoding="utf-8") as f:
                if schema_file.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                else:
                    import json
                    data = json.load(f)
            
            slides = data.get("presentation", {}).get("slides", [])
            if slides:
                click.echo(f"Slides: {len(slides)}")
        except Exception:
            pass  # Ignore errors in counting

