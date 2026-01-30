"""Tests for airops.publish.loader module."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from airops.errors import ToolLoadError
from airops.publish.loader import LoadedTool, load_tool


class TestLoadTool:
    """Tests for load_tool function."""

    def test_loads_valid_tool(self, tmp_path: Path, mock_env: None) -> None:
        """Loads a valid tool.py and extracts metadata."""
        tool_file = tmp_path / "tool.py"
        tool_file.write_text(
            dedent("""
            from pydantic import Field
            from airops import Tool
            from airops.inputs import ToolInputs, ShortText
            from airops.outputs import ToolOutputs

            class Inputs(ToolInputs):
                query: ShortText = Field(..., description="Search query")

            class Outputs(ToolOutputs):
                results: list[str]

            tool = Tool(
                name="test_tool",
                description="A test tool",
                input_model=Inputs,
                output_model=Outputs,
            )

            @tool.handler
            async def run(inputs: Inputs) -> Outputs:
                return Outputs(results=["result1", "result2"])
            """)
        )

        loaded = load_tool(tool_file)

        assert isinstance(loaded, LoadedTool)
        assert loaded.name == "test_tool"
        assert loaded.description == "A test tool"
        assert "properties" in loaded.inputs_schema
        assert "query" in loaded.inputs_schema["properties"]
        assert "properties" in loaded.outputs_schema
        assert "results" in loaded.outputs_schema["properties"]

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        """Raises ToolLoadError for missing file."""
        tool_file = tmp_path / "nonexistent.py"

        with pytest.raises(ToolLoadError, match="Tool file not found"):
            load_tool(tool_file)

    def test_raises_for_directory(self, tmp_path: Path) -> None:
        """Raises ToolLoadError when path is a directory."""
        with pytest.raises(ToolLoadError, match="is not a file"):
            load_tool(tmp_path)

    def test_raises_for_no_tool_instance(self, tmp_path: Path) -> None:
        """Raises ToolLoadError when no Tool instance found."""
        tool_file = tmp_path / "tool.py"
        tool_file.write_text(
            dedent("""
            # No Tool instance here
            x = 42
            """)
        )

        with pytest.raises(ToolLoadError, match="No Tool instance found"):
            load_tool(tool_file)

    def test_raises_for_multiple_tools(self, tmp_path: Path, mock_env: None) -> None:
        """Raises ToolLoadError when multiple Tool instances found."""
        tool_file = tmp_path / "tool.py"
        tool_file.write_text(
            dedent("""
            from airops import Tool
            from airops.inputs import ToolInputs
            from airops.outputs import ToolOutputs

            class Inputs(ToolInputs):
                pass

            class Outputs(ToolOutputs):
                pass

            tool1 = Tool(
                name="tool1",
                description="First tool",
                input_model=Inputs,
                output_model=Outputs,
            )

            tool2 = Tool(
                name="tool2",
                description="Second tool",
                input_model=Inputs,
                output_model=Outputs,
            )
            """)
        )

        with pytest.raises(ToolLoadError, match="Multiple Tool instances found"):
            load_tool(tool_file)

    def test_raises_for_syntax_error(self, tmp_path: Path) -> None:
        """Raises ToolLoadError for Python syntax errors."""
        tool_file = tmp_path / "tool.py"
        tool_file.write_text("def broken(")

        with pytest.raises(ToolLoadError, match="Failed to load module"):
            load_tool(tool_file)

    def test_raises_for_import_error(self, tmp_path: Path) -> None:
        """Raises ToolLoadError for import errors."""
        tool_file = tmp_path / "tool.py"
        tool_file.write_text("import nonexistent_module_xyz")

        with pytest.raises(ToolLoadError, match="Failed to load module"):
            load_tool(tool_file)


class TestLoadedTool:
    """Tests for LoadedTool dataclass."""

    def test_loaded_tool_fields(self) -> None:
        """LoadedTool has expected fields."""
        loaded = LoadedTool(
            name="test",
            description="Test tool",
            inputs_schema={"properties": {}},
            outputs_schema={"properties": {}},
        )

        assert loaded.name == "test"
        assert loaded.description == "Test tool"
        assert loaded.inputs_schema == {"properties": {}}
        assert loaded.outputs_schema == {"properties": {}}
