"""Tests for airops.publish.builder module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from airops.errors import DockerBuildError, DockerNotFoundError, TypeCheckError
from airops.publish.builder import (
    BuildResult,
    build_and_export,
    build_image,
    check_docker_available,
    cleanup_image,
    export_image,
    run_type_check,
)


class TestCheckDockerAvailable:
    """Tests for check_docker_available function."""

    def test_succeeds_when_docker_running(self) -> None:
        """Passes when Docker daemon is running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            check_docker_available()

    def test_raises_when_docker_not_running(self) -> None:
        """Raises DockerNotFoundError when Docker daemon not running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            with pytest.raises(DockerNotFoundError, match="not running"):
                check_docker_available()

    def test_raises_when_docker_not_installed(self) -> None:
        """Raises DockerNotFoundError when Docker not installed."""
        with (
            patch("subprocess.run", side_effect=FileNotFoundError),
            pytest.raises(DockerNotFoundError, match="not installed"),
        ):
            check_docker_available()

    def test_raises_when_docker_times_out(self) -> None:
        """Raises DockerNotFoundError when Docker command times out."""
        with (
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 10)),
            pytest.raises(DockerNotFoundError, match="not responding"),
        ):
            check_docker_available()


class TestBuildImage:
    """Tests for build_image function."""

    def test_returns_image_tag_on_success(self, tmp_path: Path) -> None:
        """Returns image tag when build succeeds."""
        with (
            patch("airops.publish.builder.check_docker_available"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            tag = build_image(tmp_path, "my_tool")

            assert tag.startswith("airops-tool-my_tool-")
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert cmd[:4] == ["docker", "build", "--platform", "linux/amd64"]

    def test_raises_on_build_failure(self, tmp_path: Path) -> None:
        """Raises DockerBuildError when build fails."""
        with (
            patch("airops.publish.builder.check_docker_available"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Build error: file not found",
            )

            with pytest.raises(DockerBuildError, match="Build error"):
                build_image(tmp_path, "my_tool")


class TestExportImage:
    """Tests for export_image function."""

    def test_returns_tarball_path_on_success(self, tmp_path: Path) -> None:
        """Returns tarball path when export succeeds."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            tarball_path = export_image("my-image:latest", tmp_path)

            assert tarball_path.parent == tmp_path
            assert tarball_path.suffix == ".tar"
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0][:2] == ["docker", "save"]

    def test_raises_on_export_failure(self, tmp_path: Path) -> None:
        """Raises DockerBuildError when export fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Save error: image not found",
            )

            with pytest.raises(DockerBuildError, match="Save error"):
                export_image("nonexistent:latest", tmp_path)


class TestCleanupImage:
    """Tests for cleanup_image function."""

    def test_removes_image(self) -> None:
        """Calls docker rmi to remove image."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            cleanup_image("my-image:latest")

            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["docker", "rmi", "my-image:latest"]

    def test_ignores_removal_failure(self) -> None:
        """Does not raise on removal failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            # Should not raise
            cleanup_image("my-image:latest")


class TestBuildAndExport:
    """Tests for build_and_export function."""

    def test_returns_build_result(self, tmp_path: Path) -> None:
        """Returns BuildResult with all fields."""
        tarball_file = tmp_path / "test.tar"
        tarball_file.write_bytes(b"fake tarball content")

        with patch("airops.publish.builder.build_image") as mock_build:
            mock_build.return_value = "airops-tool-test-12345"

            with patch("airops.publish.builder.export_image") as mock_export:
                mock_export.return_value = tarball_file

                result = build_and_export(tmp_path, "test")

                assert isinstance(result, BuildResult)
                assert result.image_tag == "airops-tool-test-12345"
                assert result.tarball_path == tarball_file
                assert result.tarball_size == len(b"fake tarball content")


class TestRunTypeCheck:
    """Tests for run_type_check function."""

    def test_succeeds_when_mypy_passes(self, tmp_path: Path) -> None:
        """Passes when mypy returns success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            run_type_check(tmp_path)

    def test_raises_when_mypy_fails(self, tmp_path: Path) -> None:
        """Raises TypeCheckError when mypy finds errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="tool.py:10: error: Incompatible types",
                stderr="",
            )
            with pytest.raises(TypeCheckError, match="Incompatible types"):
                run_type_check(tmp_path)

    def test_raises_when_mypy_not_installed(self, tmp_path: Path) -> None:
        """Raises TypeCheckError when mypy not installed."""
        with (
            patch("subprocess.run", side_effect=FileNotFoundError),
            pytest.raises(TypeCheckError, match="not installed"),
        ):
            run_type_check(tmp_path)

    def test_raises_when_mypy_times_out(self, tmp_path: Path) -> None:
        """Raises TypeCheckError when mypy times out."""
        with (
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("mypy", 120)),
            pytest.raises(TypeCheckError, match="timed out"),
        ):
            run_type_check(tmp_path)


class TestBuildResult:
    """Tests for BuildResult dataclass."""

    def test_build_result_fields(self, tmp_path: Path) -> None:
        """BuildResult has expected fields."""
        tarball = tmp_path / "test.tar"
        tarball.touch()

        result = BuildResult(
            image_tag="my-image:latest",
            tarball_path=tarball,
            tarball_size=1024,
        )

        assert result.image_tag == "my-image:latest"
        assert result.tarball_path == tarball
        assert result.tarball_size == 1024
