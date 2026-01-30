"""Implementation of the 'airops publish' command."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TransferSpeedColumn,
)

from airops.errors import (
    AiropsError,
    DockerBuildError,
    DockerNotFoundError,
    PublishFailedError,
    PublishTimeoutError,
    ToolLoadError,
    TypeCheckError,
)
from airops.publish.builder import build_and_export, cleanup_image, run_type_check
from airops.publish.client import PublishClient
from airops.publish.loader import load_tool

console = Console()


def run_publish(name: str | None, description: str | None, timeout: int) -> int:
    """Publish tool to AirOps.

    Args:
        name: Tool name override (or None to use from tool.py).
        description: Tool description override (or None to use from tool.py).
        timeout: Timeout in seconds for the publish operation.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    cwd = Path.cwd()

    # Validate required files
    if not (cwd / "Dockerfile").exists():
        console.print("[red]Error:[/red] No Dockerfile found. Run 'airops init' first.")
        return 1

    if not (cwd / "tool.py").exists():
        console.print("[red]Error:[/red] No tool.py found. Run 'airops init' first.")
        return 1

    try:
        return asyncio.run(_publish_async(cwd, name, description, timeout))
    except KeyboardInterrupt:
        console.print("\n[yellow]Publish cancelled.[/yellow]")
        return 1


async def _publish_async(
    tool_dir: Path,
    name_override: str | None,
    description_override: str | None,
    timeout: int,
) -> int:
    """Async implementation of the publish flow."""
    tool_path = tool_dir / "tool.py"

    # Step 1: Load tool metadata
    console.print("\n[bold][1/5] Loading tool metadata...[/bold]")
    try:
        loaded_tool = load_tool(tool_path)
    except ToolLoadError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    tool_name = name_override or loaded_tool.name
    tool_description = description_override or loaded_tool.description

    console.print(f"      Name: [cyan]{tool_name}[/cyan]")
    console.print(f"      Description: {tool_description}")
    _print_schema_summary("Inputs", loaded_tool.inputs_schema)
    _print_schema_summary("Outputs", loaded_tool.outputs_schema)

    # Step 2: Type check
    console.print("\n[bold][2/5] Running type checks...[/bold]")
    try:
        run_type_check(tool_dir)
        console.print("      [green]All checks passed[/green]")
    except TypeCheckError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    # Step 3: Build Docker image
    console.print("\n[bold][3/5] Building Docker image...[/bold]")
    try:
        build_result = build_and_export(tool_dir, tool_name)
    except DockerNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1
    except DockerBuildError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    console.print(f"      Image: [cyan]{build_result.image_tag}[/cyan]")
    console.print(f"      Size: {_format_size(build_result.tarball_size)}")

    try:
        # Step 4: Upload to AirOps
        console.print("\n[bold][4/5] Uploading to AirOps...[/bold]")

        async with PublishClient() as client:
            # Get or create tool
            tool = await client.get_or_create_tool(tool_name, tool_description)
            tool_id = tool["id"]

            # Create version with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console,
            ) as progress:
                task_id = progress.add_task(
                    "Uploading image",
                    total=build_result.tarball_size,
                )

                def update_progress(bytes_sent: int, total: int) -> None:
                    progress.update(task_id, completed=bytes_sent)

                version = await client.create_version(
                    tool_id=tool_id,
                    input_schema=loaded_tool.inputs_schema,
                    output_schema=loaded_tool.outputs_schema,
                    image_tarball=build_result.tarball_path,
                    progress_callback=update_progress,
                )

            version_id = version["id"]

            # Step 5: Wait for deployment
            console.print("\n[bold][5/5] Deploying...[/bold]")

            statuses: list[str] = []

            def on_status_change(status: str) -> None:
                statuses.append(status)
                status_line = " -> ".join(statuses)
                console.print(f"      Status: {status_line}", end="\r")

            try:
                final_version = await client.wait_for_publish(
                    tool_id=tool_id,
                    version_id=version_id,
                    timeout_s=timeout,
                    status_callback=on_status_change,
                )
            except PublishTimeoutError as e:
                console.print(f"\n[red]Error:[/red] {e}")
                return 1
            except PublishFailedError as e:
                console.print(f"\n[red]Error:[/red] {e}")
                return 1

            # Clear the status line and print final status
            console.print(" " * 80, end="\r")
            console.print(f"      Status: {' -> '.join(statuses)}")

            service_url = final_version.get("service_url")
            if service_url:
                console.print(f"      Service URL: [cyan]{service_url}[/cyan]")

        # Success message
        console.print(
            f"\n[green]Published successfully![/green]\n"
            f"Tool '[cyan]{tool_name}[/cyan]' is now available in your workspace.\n"
        )

        # MCP server access instructions
        console.print("[bold]Access via MCP Server[/bold]\n")
        console.print(
            "Your tool can be accessed through the AirOps Tools MCP server.\n"
            "Configure your MCP client with your workspace API key "
            "(found in AirOps app under Settings -> Workspace -> API KEY).\n"
        )
        console.print("[dim]Claude Desktop:[/dim]")
        console.print(
            "  claude mcp add --transport http airops-tools "
            "https://app.airops.com/internal_api/tools/mcp "
            '--header "Authorization: Bearer <YOUR_WORKSPACE_TOKEN>"\n'
        )
        console.print("[dim]Cursor (add to mcp.json):[/dim]")
        console.print(
            "  {\n"
            '    "mcpServers": {\n'
            '      "airops-tools": {\n'
            '        "url": "https://app.airops.com/internal_api/tools/mcp",\n'
            '        "headers": {\n'
            '          "Authorization": "Bearer <YOUR_WORKSPACE_TOKEN>"\n'
            "        }\n"
            "      }\n"
            "    }\n"
            "  }"
        )
        return 0

    except AiropsError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        return 1

    finally:
        # Cleanup
        if build_result.tarball_path.exists():
            build_result.tarball_path.unlink()
        cleanup_image(build_result.image_tag)


def _print_schema_summary(label: str, schema: dict[str, Any]) -> None:
    """Print a summary of input/output schema fields."""
    properties = schema.get("properties", {})
    if not properties:
        console.print(f"      {label}: (none)")
        return

    field_names = list(properties.keys())
    if len(field_names) <= 3:
        fields_str = ", ".join(field_names)
    else:
        fields_str = f"{', '.join(field_names[:3])}, ... ({len(field_names)} total)"

    console.print(f"      {label}: {fields_str}")


def _format_size(size_bytes: int) -> str:
    """Format byte size as human-readable string."""
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
