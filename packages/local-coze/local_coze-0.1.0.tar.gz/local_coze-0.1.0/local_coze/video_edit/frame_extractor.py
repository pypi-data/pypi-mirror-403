import asyncio
from typing import Dict, Optional

from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError
from .models import (
    FrameExtractorByIntervalRequest,
    FrameExtractorByKeyFrameRequest,
    FrameExtractorResponse,
)


class FrameExtractorClient(BaseClient):
    def __init__(
            self,
            config: Optional[Config] = None,
            ctx: Optional[Context] = None,
            custom_headers: Optional[Dict[str, str]] = None,
            verbose: bool = False,
    ):
        super().__init__(config, ctx, custom_headers, verbose)
        self.base_url = self.config.base_url

    @observe
    def extract_by_key_frame(self, url: str) -> FrameExtractorResponse:
        """
        按关键帧抽取视频帧

        Args:
            url: 视频 URL 链接

        Returns:
            FrameExtractorResponse: 抽帧结果响应

        Raises:
            APIError: 当抽帧失败时
        """
        request = FrameExtractorByKeyFrameRequest(url=url)

        response = self._request(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=frame_extractor_by_key_frame",
            json=request.to_api_request(),
        )

        if response.get("code") != 0:
            raise APIError(
                f"关键帧抽取失败: {response.get('message', 'Unknown error')}",
                code=response.get("code"),
            )

        return FrameExtractorResponse(**response)

    @observe
    def extract_by_interval(self, url: str, interval_ms: int) -> FrameExtractorResponse:
        """
        等时抽帧，从视频开始，每隔 interval_ms 时间抽帧一次。

        Args:
            url: 视频 URL 链接
            interval_ms: 间隔抽帧时间，单位: ms

        Returns:
            FrameExtractorResponse: 抽帧结果响应

        Raises:
            APIError: 当抽帧失败时
        """
        request = FrameExtractorByIntervalRequest(url=url, interval_ms=interval_ms)

        response = self._request(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=frame_extractor_by_interval",
            json=request.to_api_request(),
        )

        if response.get("code") != 0:
            raise APIError(
                f"间隔抽帧失败: {response.get('message', 'Unknown error')}",
                code=response.get("code"),
            )

        return FrameExtractorResponse(**response)

    @observe
    def extract_by_count(self, url: str, count: int) -> FrameExtractorResponse:
        """
        定数抽帧，根据视频时长/抽取帧数计算间隔动态抽帧。

        Args:
            url: 视频 URL 链接
            count: 抽取多少个帧

        Returns:
            FrameExtractorResponse: 抽帧结果响应

        Raises:
            APIError: 当抽帧失败时
        """
        from .models import FrameExtractorByInterval

        request = FrameExtractorByInterval(url=url, count=count)

        response = self._request(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=frame_extractor_by_count",
            json=request.to_api_request(),
        )

        if response.get("code") != 0:
            raise APIError(
                f"按数量抽帧失败: {response.get('message', 'Unknown error')}",
                code=response.get("code"),
            )

        return FrameExtractorResponse(**response)

    async def extract_by_key_frame_async(self, url: str) -> FrameExtractorResponse:
        """
        按关键帧抽取视频帧（异步版本）

        Args:
            url: 视频 URL 链接

        Returns:
            FrameExtractorResponse: 抽帧结果响应

        Raises:
            APIError: 当抽帧失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract_by_key_frame, url)

    async def extract_by_interval_async(
            self, url: str, interval_ms: int
    ) -> FrameExtractorResponse:
        """
        等时抽帧，从视频开始，每隔 interval_ms 时间抽帧一次（异步版本）

        Args:
            url: 视频 URL 链接
            interval_ms: 间隔抽帧时间，单位: ms

        Returns:
            FrameExtractorResponse: 抽帧结果响应

        Raises:
            APIError: 当抽帧失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.extract_by_interval, url, interval_ms
        )

    async def extract_by_count_async(
            self, url: str, count: int
    ) -> FrameExtractorResponse:
        """
        定数抽帧，根据视频时长/抽取帧数计算间隔动态抽帧（异步版本）

        Args:
            url: 视频 URL 链接
            count: 抽取多少个帧

        Returns:
            FrameExtractorResponse: 抽帧结果响应

        Raises:
            APIError: 当抽帧失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract_by_count, url, count)
