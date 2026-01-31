from __future__ import annotations
from typing import TYPE_CHECKING

from .base_resource import SyncAPIResource, AsyncAPIResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Artifacts(SyncAPIResource):  # type: ignore[misc]
    """
    Resource to interact with job artifacts.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)

    def download(self, artifact_id: str, destination_path: str) -> None:
        """
        Download an artifact file to a local path.

        Args:
            artifact_id: The UUID of the artifact to download.
            destination_path: Local file path where the artifact will be saved.

        Raises:
            HTTPError: If the download fails or the artifact is not found.
        """
        download_url = f"/artifacts/{artifact_id}/download"
        response = self._rest_client.get(download_url)
        response.raise_for_status()

        with open(destination_path, "wb") as f:
            f.write(response.content)


class AsyncArtifacts(AsyncAPIResource):  # type: ignore[misc]
    """
    Async resource to interact with job artifacts.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)

    async def download(self, artifact_id: str, destination_path: str) -> None:
        """
        Download an artifact file to a local path.

        Args:
            artifact_id: The UUID of the artifact to download.
            destination_path: Local file path where the artifact will be saved.

        Raises:
            HTTPError: If the download fails or the artifact is not found.
        """
        download_url = f"/artifacts/{artifact_id}/download"
        response = await self._rest_client.get(download_url)
        response.raise_for_status()

        with open(destination_path, "wb") as f:
            f.write(response.content)
