"""Pixabay service for fetching and validating stock footage."""

import logging
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Any

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


class PixabayServiceError(StockServiceError):
    """Pixabay specific service error."""

    pass


class PixabayService(CommonStockMethods):
    """Service for fetching stock footage from Pixabay API."""

    BASE_URL = "https://pixabay.com/api/videos/"

    def __init__(
        self,
        settings: "Settings",
        openai_service: "OpenAIService | None" = None,
    ) -> None:
        """Initialize the Pixabay service.

        Args:
            settings: Application settings containing API key and configuration.
            openai_service: Optional OpenAI service for video validation.
        """
        super().__init__(settings, openai_service)
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PixabayService":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=60.0)
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
            self._http_client = httpx.AsyncClient(timeout=60.0)
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
        """Search for videos on Pixabay.

        Args:
            keyword: The search keyword.
            per_page: Number of videos per page.
            page: Page number to fetch.

        Returns:
            List of StockVideo objects.
        """
        if not self.settings.pixabay_api_key:
            raise PixabayServiceError("Pixabay API key is not configured")

        if per_page is None:
            per_page = self.settings.pixabay_videos_per_query

        # Pixabay requires URL encoding for the query
        encoded_query = urllib.parse.quote(keyword)

        params = {
            "key": self.settings.pixabay_api_key,
            "q": encoded_query,
            "video_type": "all",
            "per_page": min(per_page, 200),  # Pixabay max is 200
            "page": page,
            "min_width": 1280,  # Prefer HD
            "safesearch": "true",
        }

        try:
            response = await self.http_client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            videos = []
            for hit in data.get("hits", []):
                stock_video = self._map_hit_to_stock_video(hit)
                if stock_video:
                    videos.append(stock_video)

            logger.info(f"Found {len(videos)} suitable videos for '{keyword}' on Pixabay")
            return videos

        except httpx.HTTPError as e:
            logger.error(f"Pixabay API error: {e}")
            raise PixabayServiceError(f"Failed to search Pixabay: {e}") from e

    def _map_hit_to_stock_video(self, hit: dict[str, Any]) -> StockVideo | None:
        """Map Pixabay API hit to StockVideo model."""
        video_files = []

        # Pixabay provides 'videos' object with keys 'large', 'medium', 'small', 'tiny'
        hit_videos = hit.get("videos", {})

        # Order of preference for mapping
        qualities = [
            ("large", "hd"),
            ("medium", "sd"),
            ("small", "sd"),
            ("tiny", "sd"),
        ]

        for p_quality, s_quality in qualities:
            if p_quality in hit_videos:
                v_data = hit_videos[p_quality]
                # Check for > 0 size and valid url
                if v_data.get("size", 0) > 0 and v_data.get("url"):
                    video_files.append(
                        StockVideoFile(
                            id=hit.get("id", 0),  # Use hit ID as file ID isn't distinct
                            quality=s_quality,
                            file_type="mp4",  # Pixabay usually serves mp4
                            width=v_data.get("width", 0),
                            height=v_data.get("height", 0),
                            link=v_data.get("url"),
                        )
                    )

        if not video_files:
            return None

        # Pixabay picture_id used to construct preview URL
        picture_id = hit.get("picture_id")
        preview_urls = []
        if picture_id:
            # Construct standard Vimeo preview URL used by Pixabay
            preview_urls.append(f"https://i.vimeocdn.com/video/{picture_id}_640x360.jpg")

        return StockVideo(
            id=hit.get("id", 0),
            width=hit.get("videos", {}).get("large", {}).get("width", 1920),
            height=hit.get("videos", {}).get("large", {}).get("height", 1080),
            duration=hit.get("duration", 0),
            url=hit.get("pageURL", ""),
            video_files=video_files,
            video_pictures=preview_urls,
            provider="pixabay",
        )

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
        """Download video file from Pixabay.

        Args:
            video: StockVideo object.
            output_path: Path to save the video.

        Returns:
            Path to downloaded file.
        """
        # Get best file (prefer HD)
        video_file = video.get_best_file(
            target_width=self.settings.video_width,
            target_height=self.settings.video_height,
        )

        if not video_file:
            raise PixabayServiceError(f"No suitable video file found for video {video.id}")

        logger.info(
            f"Downloading Pixabay video {video.id} ({video_file.width}x{video_file.height})"
        )

        try:
            # Ensure parent dict exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            async with self.http_client.stream("GET", video_file.link) as response:
                response.raise_for_status()

                async with aiofiles.open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await f.write(chunk)

            return output_path

        except httpx.HTTPError as e:
            logger.error(f"Failed to download Pixabay video {video.id}: {e}")
            if output_path.exists():
                output_path.unlink()
            raise PixabayServiceError(f"Failed to download video: {e}") from e
