"""Main VideoComposer class orchestrating the video generation pipeline."""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from video_composer.config import Settings, get_settings
from video_composer.models import CompositionResult, StockFootage, VideoProject
from video_composer.services.common_stock import CommonStockMethods
from video_composer.services.openai_service import OpenAIService
from video_composer.services.pexels_service import PexelsService
from video_composer.services.pixabay_service import PixabayService
from video_composer.utils.subtitles import SubtitleGenerator
from video_composer.utils.video_processor import VideoProcessor

if TYPE_CHECKING:
    from video_composer.models import Transcription

logger = logging.getLogger(__name__)


class VideoComposerError(Exception):
    """Base exception for VideoComposer errors."""

    pass


class VideoComposer:
    """Main orchestrator for social video automation.

    This class coordinates the entire video generation pipeline:
    1. Generate TTS audio from script
    2. Transcribe audio for word-level timestamps
    3. Fetch and validate stock footage for keywords
    4. Generate karaoke-style subtitles
    5. Compose final video

    Usage:
        async with VideoComposer() as composer:
            result = await composer.create_video(
                script="Your marketing script here",
                keywords=["technology", "innovation", "success"],
            )
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the VideoComposer.

        Args:
            settings: Optional settings override. Uses default settings if not provided.
        """
        self.settings = settings or get_settings()
        self.settings.ensure_directories()

        # Initialize services
        self.openai_service = OpenAIService(self.settings)
        self.stock_provider = self._get_stock_provider()
        self.subtitle_generator = SubtitleGenerator(self.settings)
        self.video_processor = VideoProcessor(self.settings)

        # Track active project
        self._current_project: VideoProject | None = None
        self._session_id: str = ""

    def _get_stock_provider(self) -> CommonStockMethods:
        """Get the configured stock footage provider."""
        if self.settings.stock_provider == "pixabay":
            logger.info("Using Pixabay as stock footage provider")
            return PixabayService(self.settings, self.openai_service)
        else:
            logger.info("Using Pexels as stock footage provider")
            return PexelsService(self.settings, self.openai_service)

    async def __aenter__(self) -> "VideoComposer":
        """Async context manager entry."""
        await self.openai_service.__aenter__()
        await self.stock_provider.__aenter__()
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
        logger.info(f"VideoComposer session started: {self._session_id}")
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.openai_service.__aexit__(exc_type, exc_val, exc_tb)
        await self.stock_provider.__aexit__(exc_type, exc_val, exc_tb)
        logger.info(f"VideoComposer session ended: {self._session_id}")

    def _get_session_dir(self) -> Path:
        """Get the temporary directory for this session."""
        session_dir = self.settings.temp_dir / self._session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    async def create_video(
        self,
        script: str,
        keywords: list[str],
        output_filename: str | None = None,
        validation_context: str | None = None,
        cleanup_temp: bool = True,
    ) -> CompositionResult:
        """Create a complete marketing video from script and keywords.

        This is the main entry point for video generation. It orchestrates
        the entire pipeline asynchronously, parallelizing where possible.

        Args:
            script: The marketing script text to convert to speech.
            keywords: List of keywords for stock footage search.
            output_filename: Optional output filename (without extension).
            validation_context: Optional context for video validation.
            cleanup_temp: Whether to clean up temporary files after.

        Returns:
            CompositionResult with success status and output path.

        Raises:
            VideoComposerError: If video creation fails.
        """
        logger.info(f"Starting video creation: {len(script)} chars, {len(keywords)} keywords")

        if not script.strip():
            raise VideoComposerError("Script cannot be empty")

        if not keywords:
            raise VideoComposerError("At least one keyword is required")

        # Initialize project
        self._current_project = VideoProject(script=script, keywords=keywords)
        session_dir = self._get_session_dir()
        warnings: list[str] = []

        try:
            # Phase 1: Generate TTS and fetch stock footage in parallel
            logger.info("Phase 1: Generating assets in parallel...")

            audio_path = session_dir / "audio.mp3"

            # Run TTS and stock footage fetching in parallel
            tts_task = self.openai_service.generate_tts(script, audio_path)
            footage_task = self.stock_provider.get_multiple_footage(
                keywords,
                session_dir / "footage",
                validation_context,
            )

            audio_result, footage_result = await asyncio.gather(
                tts_task,
                footage_task,
                return_exceptions=True,
            )

            # Handle TTS result
            if isinstance(audio_result, Exception):
                raise VideoComposerError(f"TTS generation failed: {audio_result}")
            self._current_project.audio_path = audio_result

            # Handle footage result
            if isinstance(footage_result, Exception):
                raise VideoComposerError(f"Stock footage fetching failed: {footage_result}")
            footage_map: dict[str, StockFootage] = footage_result

            # Phase 2: Transcribe audio for word timestamps
            logger.info("Phase 2: Transcribing audio...")
            transcription = await self.openai_service.transcribe_audio(audio_result)
            self._current_project.transcription = transcription

            # Phase 3: Generate subtitles
            logger.info("Phase 3: Generating subtitles...")
            subtitle_path = session_dir / "subtitles.ass"
            self.subtitle_generator.generate_subtitles(
                transcription,
                subtitle_path,
                words_per_line=4,
            )

            # Phase 4: Create video segments
            logger.info("Phase 4: Creating video segments...")

            # Order footage by keyword order
            footage_list = [footage_map[kw] for kw in keywords if kw in footage_map]

            if not footage_list:
                raise VideoComposerError("No valid footage available for video composition")

            segments = self.video_processor.create_segments_from_footage(
                footage_list,
                transcription,
            )
            self._current_project.segments = segments

            # Phase 5: Compose final video
            logger.info("Phase 5: Composing final video...")

            if output_filename is None:
                output_filename = f"video_{self._session_id}"

            output_path = self.settings.output_dir / f"{output_filename}.mp4"

            final_path = self.video_processor.compose_video(
                segments,
                audio_result,
                subtitle_path,
                output_path,
            )

            self._current_project.output_path = final_path

            # Cleanup if requested
            if cleanup_temp:
                self._cleanup_session_files(session_dir)

            logger.info(f"Video creation complete: {final_path}")

            return CompositionResult(
                success=True,
                output_path=final_path,
                duration=transcription.duration,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Video creation failed: {e}")

            if cleanup_temp:
                self._cleanup_session_files(session_dir)

            return CompositionResult(
                success=False,
                output_path=None,
                duration=0.0,
                error=str(e),
                warnings=warnings,
            )

    async def generate_tts_only(
        self,
        script: str,
        output_path: Path | None = None,
    ) -> Path:
        """Generate only TTS audio without creating a video.

        Args:
            script: Text to convert to speech.
            output_path: Optional output path for the audio file.

        Returns:
            Path to the generated audio file.
        """
        if output_path is None:
            output_path = self._get_session_dir() / "audio.mp3"

        return await self.openai_service.generate_tts(script, output_path)

    async def transcribe_audio_only(self, audio_path: Path) -> "Transcription":
        """Transcribe audio without creating a video.

        Args:
            audio_path: Path to the audio file.

        Returns:
            Transcription with word-level timestamps.
        """
        return await self.openai_service.transcribe_audio(audio_path)

    async def fetch_validated_footage(
        self,
        keywords: list[str],
        output_dir: Path | None = None,
        validation_context: str | None = None,
    ) -> dict[str, StockFootage]:
        """Fetch and validate stock footage for keywords.

        Args:
            keywords: List of keywords to search for.
            output_dir: Optional directory to save footage.
            validation_context: Optional context for validation.

        Returns:
            Dictionary mapping keywords to StockFootage.
        """
        if output_dir is None:
            output_dir = self._get_session_dir() / "footage"

        return await self.stock_provider.get_multiple_footage(
            keywords,
            output_dir,
            validation_context,
        )

    def generate_subtitles_only(
        self,
        transcription: "Transcription",
        output_path: Path | None = None,
        words_per_line: int = 4,
    ) -> Path:
        """Generate subtitles from a transcription.

        Args:
            transcription: Transcription with word timestamps.
            output_path: Optional output path for subtitle file.
            words_per_line: Words per subtitle line.

        Returns:
            Path to the generated subtitle file.
        """
        if output_path is None:
            output_path = self._get_session_dir() / "subtitles.ass"

        return self.subtitle_generator.generate_subtitles(
            transcription,
            output_path,
            words_per_line,
        )

    def _cleanup_session_files(self, session_dir: Path) -> None:
        """Clean up temporary session files.

        Args:
            session_dir: Directory to clean up.
        """
        logger.debug(f"Cleaning up session directory: {session_dir}")

        try:
            import shutil

            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.debug("Session directory cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up session directory: {e}")

    @property
    def current_project(self) -> VideoProject | None:
        """Get the current video project being processed."""
        return self._current_project

    @property
    def session_id(self) -> str:
        """Get the current session ID."""
        return self._session_id


async def create_video_simple(
    script: str,
    keywords: list[str],
    output_filename: str | None = None,
) -> CompositionResult:
    """Simple helper function to create a video without managing context.

    Args:
        script: Marketing script text.
        keywords: List of keywords for stock footage.
        output_filename: Optional output filename.

    Returns:
        CompositionResult with success status and output path.
    """
    async with VideoComposer() as composer:
        return await composer.create_video(
            script=script,
            keywords=keywords,
            output_filename=output_filename,
        )
