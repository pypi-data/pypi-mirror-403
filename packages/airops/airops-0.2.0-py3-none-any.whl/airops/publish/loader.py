"""Load tool module to extract metadata for publishing."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from airops.errors import ToolLoadError
from airops.tool import Tool


@dataclass
class LoadedTool:
    """Tool metadata extracted from tool.py module."""

    name: str
    description: str
    inputs_schema: dict[str, Any]
    outputs_schema: dict[str, Any]


def load_tool(tool_path: Path) -> LoadedTool:
    """Load tool.py and extract Tool instance metadata.

    Uses importlib to dynamically import the module and find the Tool instance.
    Does NOT call the handler or start the server.

    Args:
        tool_path: Path to the tool.py file.

    Returns:
        LoadedTool with extracted metadata.

    Raises:
        ToolLoadError: If the module cannot be loaded or no Tool instance is found.
    """
    if not tool_path.exists():
        raise ToolLoadError(f"Tool file not found: {tool_path}")

    if not tool_path.is_file():
        raise ToolLoadError(f"Tool path is not a file: {tool_path}")

    module_name = tool_path.stem
    spec = importlib.util.spec_from_file_location(module_name, tool_path)

    if spec is None or spec.loader is None:
        raise ToolLoadError(f"Cannot create module spec for: {tool_path}")

    module = importlib.util.module_from_spec(spec)

    # Add parent directory to sys.path so imports work
    parent_dir = str(tool_path.parent.resolve())
    original_path = sys.path.copy()

    try:
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Load the module
        spec.loader.exec_module(module)
    except Exception as e:
        raise ToolLoadError(f"Failed to load module {tool_path}: {e}") from e
    finally:
        sys.path = original_path

    # Find the Tool instance in the module
    tool = _find_tool_instance(module, tool_path)

    # Rebuild models to resolve forward references before accessing schemas.
    # Pass the module's namespace so type aliases (LongText, etc.) can be resolved.
    namespace = vars(module)
    try:
        tool.input_model.model_rebuild(_types_namespace=namespace)
        tool.output_model.model_rebuild(_types_namespace=namespace)
    except Exception:
        # Ignore rebuild errors - schema access will fail with a clearer message
        pass

    return LoadedTool(
        name=tool.name,
        description=tool.description,
        inputs_schema=tool.inputs_schema,
        outputs_schema=tool.outputs_schema,
    )


def _find_tool_instance(module: object, tool_path: Path) -> Tool:
    """Find the Tool instance in a loaded module.

    Args:
        module: The loaded Python module.
        tool_path: Path to the tool file (for error messages).

    Returns:
        The Tool instance found in the module.

    Raises:
        ToolLoadError: If no Tool instance or multiple Tool instances are found.
    """
    tools: list[Tool] = []

    for name in dir(module):
        if name.startswith("_"):
            continue

        obj = getattr(module, name)
        if isinstance(obj, Tool):
            tools.append(obj)

    if not tools:
        raise ToolLoadError(f"No Tool instance found in {tool_path}")

    if len(tools) > 1:
        tool_names = [t.name for t in tools]
        raise ToolLoadError(
            f"Multiple Tool instances found in {tool_path}: {tool_names}. "
            "Only one Tool instance per module is supported."
        )

    return tools[0]
