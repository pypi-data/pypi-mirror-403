"""CLI commands for GitHub Actions workflow generation."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from headless_wheel_builder.actions.generator import (
    WorkflowConfig,
    generate_workflow,
    init_workflows,
    write_workflow,
)
from headless_wheel_builder.actions.templates import (
    TEMPLATES,
    get_template,
    list_templates,
)

console = Console()


@click.group("actions")
def actions() -> None:
    """GitHub Actions workflow generator.

    Generate workflow files for CI/CD, releases, and more.
    """
    pass


@actions.command("list")
def list_cmd() -> None:
    """List available workflow templates."""
    templates = list_templates()

    table = Table(title="Available Workflow Templates")
    table.add_column("Name", style="bold cyan")
    table.add_column("Type", style="dim")
    table.add_column("Filename")
    table.add_column("Description")

    for tmpl in templates:
        table.add_row(
            tmpl.name,
            tmpl.template_type.value,
            tmpl.filename,
            tmpl.description,
        )

    console.print(table)


@actions.command("show")
@click.argument("template")
def show_cmd(template: str) -> None:
    """Show a workflow template content.

    Example:
        hwb actions show release
    """
    tmpl = get_template(template)
    if tmpl is None:
        console.print(f"[red]Unknown template:[/red] {template}")
        console.print("Use 'hwb actions list' to see available templates.")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]{tmpl.name}[/bold] - {tmpl.description}\n\n"
            f"[dim]Type:[/dim] {tmpl.template_type.value}\n"
            f"[dim]File:[/dim] {tmpl.filename}\n"
            f"[dim]Triggers:[/dim] {', '.join(tmpl.triggers)}",
            title="Template Info",
        )
    )
    console.print()
    console.print("[bold]Content:[/bold]")
    console.print(tmpl.content)


@actions.command("generate")
@click.argument("template")
@click.option("--output", "-o", "output_dir", default=".github/workflows", help="Output directory")
@click.option("--python", "-p", "python_version", default="3.12", help="Python version")
@click.option("--changelog/--no-changelog", default=True, help="Generate changelog in release")
@click.option("--dry-run", is_flag=True, help="Print content without writing")
def generate_cmd(
    template: str,
    output_dir: str,
    python_version: str,
    changelog: bool,
    dry_run: bool,
) -> None:
    """Generate a single workflow file.

    Example:
        hwb actions generate release
        hwb actions generate ci --python 3.11
    """
    tmpl = get_template(template)
    if tmpl is None:
        console.print(f"[red]Unknown template:[/red] {template}")
        sys.exit(1)

    config = WorkflowConfig(
        template=tmpl,
        output_dir=output_dir,
        python_version=python_version,
        generate_changelog=changelog,
    )

    content = generate_workflow(config)

    if dry_run:
        console.print(f"[dim]# Would write to: {output_dir}/{tmpl.filename}[/dim]")
        console.print(content)
    else:
        path = write_workflow(config, content)
        console.print(f"[green]Created:[/green] {path}")


@actions.command("init")
@click.option("--output", "-o", "output_dir", default=".github/workflows", help="Output directory")
@click.option("--python", "-p", "python_version", default="3.12", help="Python version")
@click.option("--template", "-t", "templates", multiple=True, help="Templates to generate")
@click.option("--all", "all_templates", is_flag=True, help="Generate all templates")
def init_cmd(
    output_dir: str,
    python_version: str,
    templates: tuple[str, ...],
    all_templates: bool,
) -> None:
    """Initialize GitHub Actions workflows.

    By default, creates release, ci, and publish workflows.

    Examples:
        hwb actions init
        hwb actions init --all
        hwb actions init -t release -t test
    """
    if all_templates:
        template_list = list(TEMPLATES.keys())
    elif templates:
        template_list = list(templates)
    else:
        template_list = ["release", "ci", "publish"]

    # Ensure directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    created = init_workflows(
        output_dir=output_dir,
        templates=template_list,
        python_version=python_version,
    )

    if created:
        console.print(f"[green]Created {len(created)} workflow files:[/green]")
        for path in created:
            console.print(f"  • {path}")
    else:
        console.print("[yellow]No workflows created[/yellow]")
