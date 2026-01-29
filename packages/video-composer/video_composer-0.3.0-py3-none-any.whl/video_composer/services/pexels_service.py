"""Pexels service for fetching and validating stock footage."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from video_composer.models import StockVideo, StockVideoFile
from video_composer.services.common_stock import (
    CommonStockMethods,
    StockServiceError,
)

if TYPE_CHECKING:
    from video_composer.config import Settings
    from video_composer.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class PexelsServiceError(StockServiceError):
    """Pexels specific service error."""

    pass


class PexelsService(CommonStockMethods):
    """Service for fetching stock footage from Pexels API."""

    BASE_URL = "https://api.pexels.com/videos"

    def __init__(
        self,
        settings: "Settings",
        openai_service: "OpenAIService | None" = None,
    ) -> None:
        """Initialize the Pexels service.

        Args:
            settings: Application settings containing API key and configuration.
            openai_service: Optional OpenAI service for video validation.
        """
        super().__init__(settings, openai_service)
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PexelsService":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={"Authorization": self.settings.pexels_api_key},
        )
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, ensuring it's initialized."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=60.0,
                headers={"Authorization": self.settings.pexels_api_key},
            )
        return self._http_client

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search_videos(
        self,
        keyword: str,
        per_page: int | None = None,
        page: int = 1,
    ) -> list[StockVideo]:
        """Search for videos on Pexels.

        Args:
            keyword: Search keyword/query.
            per_page: Number of results per page (defaults to settings value).
            page: Page number for pagination.

        Returns:
            List of StockVideo objects.

        Raises:
            PexelsServiceError: If the API request fails.
        """
        if per_page is None:
            per_page = self.settings.pexels_videos_per_query

        logger.info(
            f"Searching Pexels for: '{keyword}' (page {page}, per_page {per_page})"
        )

        try:
            response = await self.http_client.get(
                f"{self.BASE_URL}/search",
                params={
                    "query": keyword,
                    "per_page": per_page,
                    "page": page,
                    "orientation": self.settings.pexels_orientation,
                    "size": "large",
                },
            )
            response.raise_for_status()
            data = response.json()

            videos = []
            for video_data in data.get("videos", []):
                # Filter by minimum duration
                if video_data.get("duration", 0) < self.settings.pexels_min_duration:
                    continue

                # Parse video files
                video_files = [
                    StockVideoFile(
                        id=f.get("id", 0),
                        quality=f.get("quality", ""),
                        file_type=f.get("file_type", ""),
                        width=f.get("width", 0),
                        height=f.get("height", 0),
                        link=f.get("link", ""),
                    )
                    for f in video_data.get("video_files", [])
                ]

                # Parse video pictures (preview images)
                video_pictures = [
                    p.get("picture", "")
                    for p in video_data.get("video_pictures", [])
                    if p.get("picture")
                ]

                videos.append(
                    StockVideo(
                        id=video_data.get("id", 0),
                        width=video_data.get("width", 0),
                        height=video_data.get("height", 0),
                        duration=video_data.get("duration", 0),
                        url=video_data.get("url", ""),
                        video_files=video_files,
                        video_pictures=video_pictures,
                        provider="pexels",
                    )
                )

            logger.info(f"Found {len(videos)} suitable videos for '{keyword}'")
            return videos

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Pexels API error: {e.response.status_code} - {e.response.text}"
            )
            raise PexelsServiceError(
                f"Pexels API error: {e.response.status_code}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to search Pexels: {e}")
            raise PexelsServiceError(f"Failed to search videos: {e}") from e

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def download_video(
        self,
        video: StockVideo,
        output_path: Path,
    ) -> Path:
        """Download a video file from Pexels.

        Args:
            video: StockVideo object to download.
            output_path: Path where the video will be saved.

        Returns:
            Path to the downloaded video file.

        Raises:
            PexelsServiceError: If download fails.
        """
        # Get the best video file
        video_file = video.get_best_file(
            target_width=self.settings.video_width,
            target_height=self.settings.video_height,
        )

        if not video_file:
            raise PexelsServiceError(f"No suitable video file found for video {video.id}")

        logger.info(f"Downloading Pexels video {video.id}")

        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with streaming
            async with self.http_client.stream("GET", video_file.link) as response:
                response.raise_for_status()
                async with aiofiles.open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await f.write(chunk)

            return output_path

        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            raise PexelsServiceError(f"Failed to download video: {e}") from e
