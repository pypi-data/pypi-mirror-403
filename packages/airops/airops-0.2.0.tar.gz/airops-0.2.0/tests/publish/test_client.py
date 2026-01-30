"""Tests for airops.publish.client module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from airops.config import Config
from airops.errors import (
    AuthError,
    PublishFailedError,
    PublishTimeoutError,
    RateLimitedError,
    UpstreamUnavailableError,
)
from airops.publish.client import PublishClient


@pytest.fixture
def config() -> Config:
    """Create a test config."""
    return Config(
        api_token="test-token",
        api_base_url="https://test.airops.com",
        default_timeout_s=60,
        poll_interval_s=0.1,
    )


@pytest.fixture
def tarball(tmp_path: Path) -> Path:
    """Create a test tarball file."""
    tarball_path = tmp_path / "test-image.tar"
    tarball_path.write_bytes(b"fake docker image content")
    return tarball_path


class TestListTools:
    """Tests for list_tools method."""

    async def test_returns_tools_list(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Returns list of tools from API."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools",
            json=[{"id": 1, "name": "tool1"}, {"id": 2, "name": "tool2"}],
        )

        async with PublishClient(config) as client:
            tools = await client.list_tools()

        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"

    async def test_raises_auth_error_on_401(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Raises AuthError on 401 response."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools",
            status_code=401,
            text="Unauthorized",
        )

        async with PublishClient(config) as client:
            with pytest.raises(AuthError):
                await client.list_tools()


class TestCreateTool:
    """Tests for create_tool method."""

    async def test_creates_tool(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Creates a tool via API."""
        httpx_mock.add_response(
            method="POST",
            url="https://test.airops.com/internal_api/tools",
            status_code=201,
            json={"id": 1, "name": "new_tool", "description": "A new tool"},
        )

        async with PublishClient(config) as client:
            tool = await client.create_tool("new_tool", "A new tool")

        assert tool["id"] == 1
        assert tool["name"] == "new_tool"

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["tool"]["name"] == "new_tool"
        assert body["tool"]["description"] == "A new tool"


class TestGetOrCreateTool:
    """Tests for get_or_create_tool method."""

    async def test_returns_existing_tool(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Returns existing tool if found by name."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools",
            json=[{"id": 1, "name": "existing_tool", "description": "Existing"}],
        )

        async with PublishClient(config) as client:
            tool = await client.get_or_create_tool("existing_tool", "New description")

        assert tool["id"] == 1
        assert tool["name"] == "existing_tool"
        # Should not have made a POST request
        assert len(httpx_mock.get_requests()) == 1

    async def test_creates_new_tool_if_not_found(
        self, config: Config, httpx_mock: HTTPXMock
    ) -> None:
        """Creates new tool if not found by name."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools",
            json=[{"id": 1, "name": "other_tool"}],
        )
        httpx_mock.add_response(
            method="POST",
            url="https://test.airops.com/internal_api/tools",
            status_code=201,
            json={"id": 2, "name": "new_tool", "description": "New tool"},
        )

        async with PublishClient(config) as client:
            tool = await client.get_or_create_tool("new_tool", "New tool")

        assert tool["id"] == 2
        assert tool["name"] == "new_tool"
        assert len(httpx_mock.get_requests()) == 2


class TestCreateVersion:
    """Tests for create_version method."""

    async def test_creates_version_with_upload(
        self, config: Config, httpx_mock: HTTPXMock, tarball: Path
    ) -> None:
        """Creates version with multipart upload."""
        httpx_mock.add_response(
            method="POST",
            url="https://test.airops.com/internal_api/tools/1/versions",
            status_code=201,
            json={"id": 10, "version": 1, "status": "publishing"},
        )

        async with PublishClient(config) as client:
            version = await client.create_version(
                tool_id=1,
                input_schema={"properties": {"query": {"type": "string"}}},
                output_schema={"properties": {"results": {"type": "array"}}},
                image_tarball=tarball,
            )

        assert version["id"] == 10
        assert version["status"] == "publishing"

    async def test_calls_progress_callback(
        self, config: Config, httpx_mock: HTTPXMock, tarball: Path
    ) -> None:
        """Calls progress callback during upload."""
        httpx_mock.add_response(
            method="POST",
            url="https://test.airops.com/internal_api/tools/1/versions",
            status_code=201,
            json={"id": 10, "version": 1, "status": "publishing"},
        )

        progress_calls: list[tuple[int, int]] = []

        def on_progress(sent: int, total: int) -> None:
            progress_calls.append((sent, total))

        async with PublishClient(config) as client:
            await client.create_version(
                tool_id=1,
                input_schema={},
                output_schema={},
                image_tarball=tarball,
                progress_callback=on_progress,
            )

        assert len(progress_calls) > 0
        # Last call should have sent == total
        assert progress_calls[-1][0] == progress_calls[-1][1]

    async def test_raises_on_validation_error(
        self, config: Config, httpx_mock: HTTPXMock, tarball: Path
    ) -> None:
        """Raises PublishFailedError on 422 validation error."""
        httpx_mock.add_response(
            method="POST",
            url="https://test.airops.com/internal_api/tools/1/versions",
            status_code=422,
            json={"errors": {"input_schema": ["is invalid"]}},
        )

        async with PublishClient(config) as client:
            with pytest.raises(PublishFailedError, match="Validation error"):
                await client.create_version(
                    tool_id=1,
                    input_schema={},
                    output_schema={},
                    image_tarball=tarball,
                )


class TestGetVersion:
    """Tests for get_version method."""

    async def test_returns_version(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Returns version details."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "version": 1, "status": "active", "service_url": "https://..."},
        )

        async with PublishClient(config) as client:
            version = await client.get_version(1, 10)

        assert version["id"] == 10
        assert version["status"] == "active"


class TestWaitForPublish:
    """Tests for wait_for_publish method."""

    async def test_returns_on_active(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Returns when status becomes active."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "publishing"},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "deploying"},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "active", "service_url": "https://example.com"},
        )

        async with PublishClient(config) as client:
            version = await client.wait_for_publish(
                tool_id=1, version_id=10, timeout_s=10, poll_interval_s=0.01
            )

        assert version["status"] == "active"
        assert version["service_url"] == "https://example.com"

    async def test_raises_on_failed(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Raises PublishFailedError when status becomes failed."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "failed"},
        )

        async with PublishClient(config) as client:
            with pytest.raises(PublishFailedError):
                await client.wait_for_publish(
                    tool_id=1, version_id=10, timeout_s=10, poll_interval_s=0.01
                )

    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_raises_on_timeout(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Raises PublishTimeoutError when timeout reached."""
        # Always return publishing status - will be reused for multiple polls
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "publishing"},
        )

        async with PublishClient(config) as client:
            with pytest.raises(PublishTimeoutError, match="timed out"):
                await client.wait_for_publish(
                    tool_id=1, version_id=10, timeout_s=0.05, poll_interval_s=0.01
                )

    async def test_calls_status_callback(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Calls status callback on status changes."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "publishing"},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "deploying"},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools/1/versions/10",
            json={"id": 10, "status": "active"},
        )

        status_changes: list[str] = []

        async with PublishClient(config) as client:
            await client.wait_for_publish(
                tool_id=1,
                version_id=10,
                timeout_s=10,
                poll_interval_s=0.01,
                status_callback=lambda s: status_changes.append(s),
            )

        assert status_changes == ["publishing", "deploying", "active"]


class TestErrorHandling:
    """Tests for error handling."""

    async def test_raises_rate_limited_error(self, config: Config, httpx_mock: HTTPXMock) -> None:
        """Raises RateLimitedError on 429."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools",
            status_code=429,
        )

        async with PublishClient(config) as client:
            with pytest.raises(RateLimitedError):
                await client.list_tools()

    async def test_raises_upstream_error_on_500(
        self, config: Config, httpx_mock: HTTPXMock
    ) -> None:
        """Raises UpstreamUnavailableError on 500."""
        httpx_mock.add_response(
            method="GET",
            url="https://test.airops.com/internal_api/tools",
            status_code=500,
            text="Internal Server Error",
        )

        async with PublishClient(config) as client:
            with pytest.raises(UpstreamUnavailableError, match="Server error"):
                await client.list_tools()
