"""API client for AirOps tool publishing."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from airops.config import Config, get_config
from airops.errors import (
    AuthError,
    PublishFailedError,
    PublishTimeoutError,
    RateLimitedError,
    UpstreamUnavailableError,
)


class PublishClient:
    """Client for AirOps tool publishing API."""

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or get_config()
        self._client = httpx.AsyncClient(
            base_url=self._config.api_base_url,
            headers={
                "Authorization": f"Bearer {self._config.api_token}",
            },
            timeout=httpx.Timeout(30.0, read=300.0),  # Longer read timeout for uploads
        )

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all tools in the workspace.

        Returns:
            List of tool dictionaries.
        """
        response = await self._request("GET", "/internal_api/tools")
        return response.json()  # type: ignore[no-any-return]

    async def create_tool(self, name: str, description: str) -> dict[str, Any]:
        """Create a new tool.

        Args:
            name: Tool name.
            description: Tool description.

        Returns:
            Created tool dictionary.
        """
        response = await self._request(
            "POST",
            "/internal_api/tools",
            json={"tool": {"name": name, "description": description}},
        )
        return response.json()  # type: ignore[no-any-return]

    async def get_or_create_tool(self, name: str, description: str) -> dict[str, Any]:
        """Get existing tool by name or create a new one.

        Args:
            name: Tool name.
            description: Tool description.

        Returns:
            Tool dictionary.
        """
        tools = await self.list_tools()
        for tool in tools:
            if tool.get("name") == name:
                return tool

        return await self.create_tool(name, description)

    async def create_version(
        self,
        tool_id: int,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        image_tarball: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Create a new tool version with image upload.

        This automatically triggers publish on the server.

        Args:
            tool_id: ID of the tool.
            input_schema: JSON schema for inputs.
            output_schema: JSON schema for outputs.
            image_tarball: Path to the Docker image tarball.
            progress_callback: Optional callback(bytes_sent, total_bytes) for progress.

        Returns:
            Created version dictionary with status "publishing".
        """
        file_size = image_tarball.stat().st_size

        # Create a progress-tracking file wrapper if callback provided
        if progress_callback:
            file_obj: Any = _ProgressFile(
                image_tarball.open("rb"),
                file_size,
                progress_callback,
            )
        else:
            file_obj = image_tarball.open("rb")

        try:
            # Send schemas as JSON strings - Rails will parse them
            data = {
                "tool_version[input_schema]": json.dumps(input_schema),
                "tool_version[output_schema]": json.dumps(output_schema),
            }

            files = {
                "tool_version[provided_image]": (
                    image_tarball.name,
                    file_obj,
                    "application/x-tar",
                ),
            }

            response = await self._client.post(
                f"/internal_api/tools/{tool_id}/versions",
                data=data,
                files=files,
            )
            self._handle_response(response, [201])
            return response.json()  # type: ignore[no-any-return]
        finally:
            file_obj.close()

    async def get_version(self, tool_id: int, version_id: int) -> dict[str, Any]:
        """Get version status.

        Args:
            tool_id: ID of the tool.
            version_id: ID of the version.

        Returns:
            Version dictionary with current status.
        """
        response = await self._request(
            "GET",
            f"/internal_api/tools/{tool_id}/versions/{version_id}",
        )
        return response.json()  # type: ignore[no-any-return]

    async def wait_for_publish(
        self,
        tool_id: int,
        version_id: int,
        timeout_s: int = 600,
        poll_interval_s: float = 5.0,
        status_callback: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Poll until version is active or failed.

        Args:
            tool_id: ID of the tool.
            version_id: ID of the version.
            timeout_s: Maximum time to wait in seconds.
            poll_interval_s: Time between polls in seconds.
            status_callback: Optional callback(status) when status changes.

        Returns:
            Final version dictionary.

        Raises:
            PublishTimeoutError: If timeout is reached.
            PublishFailedError: If publish fails.
        """
        start_time = time.monotonic()
        last_status = None

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > timeout_s:
                raise PublishTimeoutError(
                    f"Publish timed out after {timeout_s} seconds. Last status: {last_status}"
                )

            version = await self.get_version(tool_id, version_id)
            status: str | None = version.get("status")

            if status != last_status:
                last_status = status
                if status_callback and status is not None:
                    status_callback(status)

            if status == "active":
                return version

            if status == "failed":
                raise PublishFailedError("Publish failed. Check the AirOps dashboard for details.")

            await asyncio.sleep(poll_interval_s)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make an HTTP request.

        Args:
            method: HTTP method.
            path: Request path.
            json: JSON body.

        Returns:
            HTTP response.
        """
        try:
            response = await self._client.request(method, path, json=json)
        except httpx.RequestError as e:
            raise UpstreamUnavailableError(f"Network error: {e}") from e

        self._handle_response(response, [200, 201])
        return response

    def _handle_response(
        self,
        response: httpx.Response,
        success_codes: list[int],
    ) -> None:
        """Handle HTTP response and raise appropriate errors."""
        if response.status_code in success_codes:
            return

        if response.status_code in (401, 403):
            raise AuthError(f"Authentication failed: {response.status_code} - {response.text}")

        if response.status_code == 429:
            raise RateLimitedError("Rate limit exceeded")

        if response.status_code == 422:
            # Validation error from Rails
            try:
                errors = response.json()
                raise PublishFailedError(f"Validation error: {errors}")
            except Exception:
                raise PublishFailedError(f"Validation error: {response.text}") from None

        if response.status_code >= 500:
            raise UpstreamUnavailableError(
                f"Server error: {response.status_code} - {response.text}"
            )

        raise UpstreamUnavailableError(
            f"Unexpected response: {response.status_code} - {response.text}"
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> PublishClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


class _ProgressFile:
    """File wrapper that tracks read progress."""

    def __init__(
        self,
        file: Any,
        total_size: int,
        callback: Callable[[int, int], None],
    ) -> None:
        self._file = file
        self._total_size = total_size
        self._callback = callback
        self._bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        data: bytes = self._file.read(size)
        self._bytes_read += len(data)
        self._callback(self._bytes_read, self._total_size)
        return data

    def seek(self, offset: int, whence: int = 0) -> int:
        result: int = self._file.seek(offset, whence)
        if whence == 0:
            self._bytes_read = offset
        return result

    def tell(self) -> int:
        result: int = self._file.tell()
        return result

    def close(self) -> None:
        self._file.close()
