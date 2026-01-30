"""CLI command for building PowerPoint presentations."""

import sys
from pathlib import Path

import click

from slidegen import SlideGenerator


@click.command()
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output PowerPoint file path (.pptx)",
)
@click.option(
    "--theme",
    type=click.Path(exists=True, path_type=Path),
    help="Path to PowerPoint template file",
)
@click.option(
    "--theme-name",
    type=click.Choice(["default", "corporate", "dark"], case_sensitive=False),
    help="Built-in theme name",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed progress output",
)
def build_cmd(
    schema_file: Path,
    output: Path,
    theme: Path | None,
    theme_name: str | None,
    verbose: bool,
) -> None:
    """
    Build a PowerPoint presentation from a SlideGen schema file.
    
    SCHEMA_FILE: Path to the schema file (YAML or JSON) to build from
    """
    try:
        if verbose:
            click.echo(f"Loading schema: {schema_file}")
        
        # Initialize generator
        gen = SlideGenerator(
            theme=str(theme) if theme else None,
            theme_name=theme_name,
        )
        
        # Load schema
        gen.from_schema(str(schema_file))
        
        if verbose:
            slides = gen.schema.get("presentation", {}).get("slides", [])
            click.echo(f"Rendering {len(slides)} slides...")
            for i, slide_data in enumerate(slides, 1):
                layout = slide_data.get("layout", "unknown")
                click.echo(f"  [{i}/{len(slides)}] Rendering {layout} layout...")
        
        # Build presentation
        gen.build(str(output))
        
        if verbose:
            file_size = output.stat().st_size / 1024  # KB
            click.echo(f"✓ Generated: {output} ({file_size:.1f} KB)")
        else:
            click.echo(f"✓ Generated: {output}")
            
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

