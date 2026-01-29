"""Common functionality for stock footage services."""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from video_composer.models import StockFootage, StockVideo

if TYPE_CHECKING:
    from video_composer.config import Settings
    from video_composer.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class StockServiceError(Exception):
    """Base exception for stock service errors."""

    pass


class VideoNotFoundError(StockServiceError):
    """No suitable video found for the keyword."""

    pass


class VideoValidationError(StockServiceError):
    """Video failed validation."""

    pass


class CommonStockMethods(ABC):
    """Abstract base class implementing common stock footage operations."""

    def __init__(
        self,
        settings: "Settings",
        openai_service: "OpenAIService | None" = None,
    ) -> None:
        """Initialize the service.

        Args:
            settings: Application settings.
            openai_service: Optional OpenAI service for validation.
        """
        self.settings = settings
        self.openai_service = openai_service

    @abstractmethod
    async def search_videos(
        self,
        keyword: str,
        per_page: int | None = None,
        page: int = 1,
    ) -> list[StockVideo]:
        """Search for videos. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def download_video(
        self,
        video: StockVideo,
        output_path: Path,
    ) -> Path:
        """Download video. Must be implemented by subclasses."""
        pass

    async def get_validated_footage(
        self,
        keyword: str,
        output_dir: Path,
        validation_context: str | None = None,
        max_attempts: int | None = None,
    ) -> StockFootage:
        """Get stock footage that has been validated to match the keyword.

        This method:
        1. Searches for videos matching the keyword
        2. Downloads each candidate
        3. Extracts a frame and validates with GPT-4 Vision
        4. If all videos fail, generates alternative keyword and retries
        5. Returns the first video that passes validation

        Args:
            keyword: Search keyword for the footage.
            output_dir: Directory to save downloaded videos.
            validation_context: Optional context for validation.
            max_attempts: Maximum keyword variations to try before giving up.

        Returns:
            StockFootage object with validated video.

        Raises:
            VideoNotFoundError: If no valid video could be found.
        """
        if max_attempts is None:
            max_attempts = self.settings.max_retries

        # Import here to avoid circular dependency
        from video_composer.utils.video_processor import VideoProcessor

        current_keyword = keyword
        tried_keywords: list[str] = []
        videos_per_keyword = 3  # Try 3 videos per keyword variant

        for attempt in range(max_attempts):
            logger.info(
                f"Getting validated footage for keyword: '{current_keyword}' "
                f"(attempt {attempt + 1}/{max_attempts})"
            )
            tried_keywords.append(current_keyword)

            # Search for videos with current keyword
            try:
                videos = await self.search_videos(current_keyword)
            except Exception as e:
                logger.warning(f"Search failed for '{current_keyword}': {e}")
                videos = []

            if not videos:
                logger.warning(f"No videos found for keyword: '{current_keyword}'")
            else:
                # Try videos from this search
                for video_idx, video in enumerate(videos[:videos_per_keyword], 1):
                    logger.info(
                        f"Trying video {video.id} ({video_idx}/{min(len(videos), videos_per_keyword)})"
                    )

                    # Download the video
                    video_path = output_dir / f"{video.provider}_{video.id}.mp4"
                    try:
                        await self.download_video(video, video_path)
                    except Exception as e:
                        logger.warning(f"Failed to download video {video.id}: {e}")
                        continue

                    # Skip validation if no OpenAI service configured
                    if self.openai_service is None:
                        logger.info("No OpenAI service configured, skipping validation")
                        return StockFootage(
                            keyword=keyword,  # Return original keyword
                            video=video,
                            local_path=video_path,
                            validation_score=1.0,
                            is_validated=False,
                        )

                    # Extract a frame for validation
                    try:
                        frame_position = min(
                            video.duration * self.settings.validation_frame_position,
                            video.duration - 1,
                        )
                        # Ensure we're in the 20-30% range as specified
                        frame_position = max(
                            video.duration * 0.2,
                            min(frame_position, video.duration * 0.3),
                        )

                        frame_path = output_dir / f"frame_{video.id}.jpg"
                        VideoProcessor.extract_frame(video_path, frame_path, frame_position)

                        # Validate with Vision
                        is_valid, confidence, explanation = await self.openai_service.validate_video_frame(
                            frame_path,
                            keyword,  # Validate against original keyword concept
                            validation_context,
                        )

                        # Clean up frame
                        if frame_path.exists():
                            frame_path.unlink()

                        if is_valid and confidence >= 0.6:
                            logger.info(
                                f"Video {video.id} validated successfully "
                                f"(confidence: {confidence:.2f})"
                            )
                            return StockFootage(
                                keyword=keyword,  # Return original keyword
                                video=video,
                                local_path=video_path,
                                validation_score=confidence,
                                is_validated=True,
                            )
                        else:
                            logger.info(f"Video {video.id} failed validation: {explanation}")
                            # Clean up the video file
                            if video_path.exists():
                                video_path.unlink()

                    except Exception as e:
                        logger.warning(f"Error validating video {video.id}: {e}")
                        # Clean up on error
                        if video_path.exists():
                            video_path.unlink()
                        continue

            # All videos failed for this keyword - generate alternative
            if attempt < max_attempts - 1 and self.openai_service is not None:
                logger.info(f"All videos failed for '{current_keyword}', generating alternative...")
                current_keyword = await self.openai_service.generate_alternative_keyword(
                    original_keyword=keyword,
                    failed_keywords=tried_keywords,
                    context=validation_context,
                )
            elif attempt < max_attempts - 1:
                # No OpenAI service, try simplifying the keyword
                words = current_keyword.split()
                if len(words) > 2:
                    current_keyword = " ".join(words[:2])
                else:
                    break  # Can't simplify further

        raise VideoNotFoundError(
            f"No valid video found for keyword '{keyword}' after {max_attempts} attempts. "
            f"Tried keywords: {', '.join(tried_keywords)}"
        )

    async def get_multiple_footage(
        self,
        keywords: list[str],
        output_dir: Path,
        validation_context: str | None = None,
    ) -> dict[str, StockFootage]:
        """Get validated footage for multiple keywords in parallel.

        Args:
            keywords: List of keywords to search for.
            output_dir: Directory to save downloaded videos.
            validation_context: Optional context for validation.

        Returns:
            Dictionary mapping keywords to their StockFootage.

        Raises:
            VideoNotFoundError: If any keyword fails to find valid footage.
        """
        tasks = [
            self.get_validated_footage(keyword, output_dir, validation_context)
            for keyword in keywords
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        footage_map: dict[str, StockFootage] = {}
        errors: list[str] = []

        for keyword, result in zip(keywords, results, strict=True):
            if isinstance(result, Exception):
                errors.append(f"'{keyword}': {result}")
            else:
                footage_map[keyword] = result

        if errors:
            error_msg = "Failed to get footage for keywords: " + "; ".join(errors)
            logger.error(error_msg)
            raise VideoNotFoundError(error_msg)

        return footage_map
