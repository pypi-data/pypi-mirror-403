# type: ignore

from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel

from adaptive_sdk.graphql_client import ResizePartitionInput, HarmonyStatus

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class ResizeResult(BaseModel):
    harmony_group_key: str
    success: bool
    error: str | None = None


class ComputePools(SyncAPIResource, UseCaseResource):
    """
    Resource to interact with compute pools.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self):
        return self._gql_client.list_compute_pools().compute_pools

    def resize_inference_partition(self, compute_pool_key: str, size: int) -> list[ResizeResult]:
        """
        Resize the inference partitions of all harmony groups in a compute pool.
        """
        cps = self.list()
        found_cp = False
        for cp in cps:
            if cp.key == compute_pool_key:
                selected_cp = cp
                found_cp = True
                break
        if not found_cp:
            raise ValueError(f"Compute pool with key {compute_pool_key} not found")

        resize_results: list[ResizeResult] = []
        for hg in selected_cp.harmony_groups:
            if hg.status == HarmonyStatus.ONLINE:
                input = ResizePartitionInput(harmonyGroup=hg.key, size=size)
                try:
                    _ = self._gql_client.resize_inference_partition(input)
                    resize_results.append(ResizeResult(harmony_group_key=hg.key, success=True))
                except Exception as e:
                    resize_results.append(ResizeResult(harmony_group_key=hg.key, success=False, error_message=str(e)))

        return resize_results


class AsyncComputePools(AsyncAPIResource, UseCaseResource):
    """
    Resource to interact with compute pools.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self):
        return (await self._gql_client.list_compute_pools()).compute_pools

    async def resize_inference_partition(self, compute_pool_key: str, size: int) -> list[ResizeResult]:
        """
        Resize the inference partitions of all harmony groups in a compute pool.
        """
        cps = await self.list()
        found_cp = False
        for cp in cps:
            if cp.key == compute_pool_key:
                selected_cp = cp
                found_cp = True
                break
        if not found_cp:
            raise ValueError(f"Compute pool with key {compute_pool_key} not found")

        resize_results: list[ResizeResult] = []
        for hg in selected_cp.harmony_groups:
            if hg.status == HarmonyStatus.ONLINE:
                input = ResizePartitionInput(harmonyGroup=hg.key, size=size)
                try:
                    _ = await self._gql_client.resize_inference_partition(input)
                    resize_results.append(ResizeResult(harmony_group_key=hg.key, success=True))
                except Exception as e:
                    resize_results.append(ResizeResult(harmony_group_key=hg.key, success=False, error_message=str(e)))

        return resize_results
