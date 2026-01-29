"""Stock provider protocol and factory for video footage services."""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from video_composer.models import StockFootage, StockVideo


@runtime_checkable
class StockProvider(Protocol):
    """Protocol defining the interface for stock video providers.

    Both PexelsService and PixabayService implement this interface,
    allowing them to be used interchangeably in the video composer.
    """

    async def search_videos(
        self,
        keyword: str,
        per_page: int | None = None,
        page: int = 1,
    ) -> list["StockVideo"]:
        """Search for videos matching the keyword.

        Args:
            keyword: Search term for videos.
            per_page: Number of results per page.
            page: Page number to fetch.

        Returns:
            List of StockVideo objects.
        """
        ...

    async def download_video(
        self,
        video: "StockVideo",
        output_path: Path,
    ) -> Path:
        """Download a video to the specified path.

        Args:
            video: The StockVideo to download.
            output_path: Where to save the downloaded video.

        Returns:
            Path to the downloaded video file.
        """
        ...

    async def get_validated_footage(
        self,
        keyword: str,
        output_dir: Path,
        validation_context: str | None = None,
        max_attempts: int | None = None,
    ) -> "StockFootage":
        """Get validated footage for a keyword.

        Searches for videos, validates them using AI vision, and returns
        the first valid match.

        Args:
            keyword: Search term for videos.
            output_dir: Directory to save downloaded video.
            validation_context: Optional context for AI validation.
            max_attempts: Maximum validation attempts.

        Returns:
            StockFootage object with validated video.

        Raises:
            VideoNotFoundError: If no valid video found after max attempts.
        """
        ...

    async def get_multiple_footage(
        self,
        keywords: list[str],
        output_dir: Path,
        validation_context: str | None = None,
    ) -> dict[str, "StockFootage"]:
        """Get validated footage for multiple keywords.

        Args:
            keywords: List of search terms.
            output_dir: Directory to save downloaded videos.
            validation_context: Optional context for AI validation.

        Returns:
            Dictionary mapping keywords to StockFootage.
        """
        ...

    async def __aenter__(self) -> "StockProvider":
        """Async context manager entry."""
        ...

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        ...
