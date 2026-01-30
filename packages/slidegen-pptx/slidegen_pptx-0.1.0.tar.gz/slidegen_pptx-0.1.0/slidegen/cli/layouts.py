"""CLI command for listing available layouts."""

import click

from slidegen.core.registry import LayoutRegistry
from slidegen.layouts import (
    BlankLayoutRenderer,
    BulletListLayoutRenderer,
    ChartLayoutRenderer,
    ComparisonLayoutRenderer,
    ImageLayoutRenderer,
    QuoteLayoutRenderer,
    SectionHeaderLayoutRenderer,
    TableLayoutRenderer,
    TitleLayoutRenderer,
    TwoColumnLayoutRenderer,
)


LAYOUT_DESCRIPTIONS = {
    "title": "Title slide with title and optional subtitle",
    "section_header": "Section divider with centered text",
    "bullet_list": "Title with bullet points (supports nested bullets)",
    "two_column": "Side-by-side content (supports bullet lists and text)",
    "chart": "Title with data visualization (bar, line, pie, column)",
    "table": "Title with data table",
    "comparison": "Before/after or option A/B comparison layout",
    "image": "Title with image (auto-scaling and centering)",
    "quote": "Large centered quote with optional attribution",
    "blank": "Empty slide for custom content",
}


def _register_all_layouts(registry: LayoutRegistry) -> None:
    """Register all layouts for listing."""
    registry.register("title", TitleLayoutRenderer())
    registry.register("section_header", SectionHeaderLayoutRenderer())
    registry.register("bullet_list", BulletListLayoutRenderer())
    registry.register("two_column", TwoColumnLayoutRenderer())
    registry.register("chart", ChartLayoutRenderer())
    registry.register("table", TableLayoutRenderer())
    registry.register("comparison", ComparisonLayoutRenderer())
    registry.register("image", ImageLayoutRenderer())
    registry.register("quote", QuoteLayoutRenderer())
    registry.register("blank", BlankLayoutRenderer())


@click.command()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed layout information",
)
def layouts_cmd(verbose: bool) -> None:
    """
    List all available slide layouts with descriptions.
    """
    registry = LayoutRegistry()
    _register_all_layouts(registry)
    
    layouts = registry.list_layouts()
    layouts.sort()
    
    click.echo("Available Layouts:")
    click.echo("")
    
    for layout in layouts:
        description = LAYOUT_DESCRIPTIONS.get(layout, "No description available")
        click.echo(f"  {layout:20} - {description}")
    
    if verbose:
        click.echo("")
        click.echo("Examples:")
        click.echo("")
        click.echo("  title:")
        click.echo("    - layout: title")
        click.echo('      title: "My Title"')
        click.echo('      subtitle: "My Subtitle"')
        click.echo("")
        click.echo("  bullet_list:")
        click.echo("    - layout: bullet_list")
        click.echo('      title: "Key Points"')
        click.echo("      bullets:")
        click.echo('        - "First point"')
        click.echo('        - "Second point"')
        click.echo("")
        click.echo("  two_column:")
        click.echo("    - layout: two_column")
        click.echo('      title: "Comparison"')
        click.echo("      left:")
        click.echo("        type: bullet_list")
        click.echo("        bullets:")
        click.echo('          - "Left point"')
        click.echo("      right:")
        click.echo("        type: bullet_list")
        click.echo("        bullets:")
        click.echo('          - "Right point"')

