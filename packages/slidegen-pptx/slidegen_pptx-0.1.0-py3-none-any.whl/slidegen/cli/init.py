"""CLI command for initializing a new SlideGen project."""

from pathlib import Path

import click

SAMPLE_SCHEMA = """presentation:
  title: "My Presentation"
  theme: "default"
  slides:
    - layout: title
      title: "Welcome"
      subtitle: "Getting Started with SlideGen"
    
    - layout: section_header
      text: "Introduction"
    
    - layout: bullet_list
      title: "Key Points"
      bullets:
        - "First important point"
        - "Second important point"
        - "Third important point"
    
    - layout: two_column
      title: "Comparison"
      left:
        type: bullet_list
        bullets:
          - "Left side point 1"
          - "Left side point 2"
      right:
        type: bullet_list
        bullets:
          - "Right side point 1"
          - "Right side point 2"
    
    - layout: title
      title: "Thank You"
      subtitle: "Questions?"
"""


@click.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=Path("presentation.yaml"),
    help="Output schema file path (default: presentation.yaml)",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing file if it exists",
)
def init_cmd(output: Path, force: bool) -> None:
    """
    Initialize a new SlideGen project with a sample schema file.
    """
    if output.exists() and not force:
        click.echo(f"Error: File {output} already exists. Use --force to overwrite.", err=True)
        return
    
    try:
        output.write_text(SAMPLE_SCHEMA, encoding="utf-8")
        click.echo(f"✓ Created sample schema: {output}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Edit {output} to customize your presentation")
        click.echo(f"  2. Run: slidegen validate {output}")
        click.echo(f"  3. Run: slidegen build {output} -o output.pptx")
    except Exception as e:
        click.echo(f"Error creating file: {e}", err=True)

