"""Docker image building and export for publishing."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from airops.errors import DockerBuildError, DockerNotFoundError, TypeCheckError


@dataclass
class BuildResult:
    """Result of Docker build and export."""

    image_tag: str
    tarball_path: Path
    tarball_size: int


def run_type_check(tool_dir: Path) -> None:
    """Run mypy type checking on the tool directory.

    Args:
        tool_dir: Directory containing the tool code.

    Raises:
        TypeCheckError: If type checking fails.
    """
    import sys

    # Use the same Python that's running this script to ensure mypy
    # has access to the same packages in the venv
    python_path = sys.executable

    try:
        result = subprocess.run(
            [python_path, "-m", "mypy", "."],
            cwd=tool_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise TypeCheckError("mypy is not installed. Install it with: pip install mypy") from None
    except subprocess.TimeoutExpired:
        raise TypeCheckError("Type checking timed out after 120 seconds") from None

    if result.returncode != 0:
        # Format the error output nicely
        error_output = result.stdout.strip() or result.stderr.strip()
        raise TypeCheckError(f"Type checking failed:\n{error_output}")


def check_docker_available() -> None:
    """Check if Docker daemon is available.

    Raises:
        DockerNotFoundError: If Docker is not available.
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise DockerNotFoundError(
                "Docker daemon is not running. Please start Docker and try again."
            )
    except FileNotFoundError:
        raise DockerNotFoundError(
            "Docker is not installed. Please install Docker and try again."
        ) from None
    except subprocess.TimeoutExpired:
        raise DockerNotFoundError(
            "Docker daemon is not responding. Please check Docker and try again."
        ) from None


def build_image(tool_dir: Path, tool_name: str) -> str:
    """Build Docker image from tool directory.

    Args:
        tool_dir: Directory containing Dockerfile and tool code.
        tool_name: Name of the tool (used in image tag).

    Returns:
        Image tag for the built image.

    Raises:
        DockerBuildError: If the build fails.
    """
    check_docker_available()

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    image_tag = f"airops-tool-{tool_name}-{timestamp}"

    result = subprocess.run(
        ["docker", "build", "--platform", "linux/amd64", "-t", image_tag, "."],
        cwd=tool_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise DockerBuildError(f"Docker build failed:\n{result.stderr}")

    return image_tag


def export_image(image_tag: str, output_dir: Path | None = None) -> Path:
    """Export Docker image to tarball using 'docker save'.

    Args:
        image_tag: Tag of the image to export.
        output_dir: Directory to save the tarball (uses temp dir if None).

    Returns:
        Path to the tarball file.

    Raises:
        DockerBuildError: If the export fails.
    """
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir())

    tarball_path = output_dir / f"{image_tag}.tar"

    result = subprocess.run(
        ["docker", "save", "-o", str(tarball_path), image_tag],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise DockerBuildError(f"Docker save failed:\n{result.stderr}")

    return tarball_path


def cleanup_image(image_tag: str) -> None:
    """Remove Docker image after publishing.

    Args:
        image_tag: Tag of the image to remove.
    """
    subprocess.run(
        ["docker", "rmi", image_tag],
        capture_output=True,
        text=True,
    )


def build_and_export(tool_dir: Path, tool_name: str) -> BuildResult:
    """Build Docker image and export to tarball.

    This is the main entry point for the builder module.

    Args:
        tool_dir: Directory containing Dockerfile and tool code.
        tool_name: Name of the tool.

    Returns:
        BuildResult with image tag, tarball path, and size.

    Raises:
        DockerNotFoundError: If Docker is not available.
        DockerBuildError: If build or export fails.
    """
    image_tag = build_image(tool_dir, tool_name)
    tarball_path = export_image(image_tag)
    tarball_size = tarball_path.stat().st_size

    return BuildResult(
        image_tag=image_tag,
        tarball_path=tarball_path,
        tarball_size=tarball_size,
    )
