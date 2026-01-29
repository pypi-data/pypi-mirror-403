"""OpenAI service for TTS, Whisper transcription, and Vision validation."""

import asyncio
import base64
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from video_composer.models import Transcription, WordTimestamp

if TYPE_CHECKING:
    from video_composer.config import Settings

logger = logging.getLogger(__name__)


class OpenAIServiceError(Exception):
    """Base exception for OpenAI service errors."""

    pass


class TTSError(OpenAIServiceError):
    """Error during text-to-speech generation."""

    pass


class TranscriptionError(OpenAIServiceError):
    """Error during audio transcription."""

    pass


class VisionError(OpenAIServiceError):
    """Error during vision analysis."""

    pass


class OpenAIService:
    """Service for interacting with OpenAI APIs (TTS, Whisper, Vision)."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the OpenAI service.

        Args:
            settings: Application settings containing API key and configuration.
        """
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OpenAIService":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=120.0)
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def generate_tts(self, text: str, output_path: Path) -> Path:
        """Generate text-to-speech audio using OpenAI's TTS API.

        Args:
            text: The text to convert to speech.
            output_path: Path where the audio file will be saved.

        Returns:
            Path to the generated audio file.

        Raises:
            TTSError: If TTS generation fails.
        """
        logger.info(f"Generating TTS for text ({len(text)} chars)")

        try:
            response = await self.client.audio.speech.create(
                model=self.settings.tts_model,
                voice=self.settings.tts_voice,
                input=text,
                speed=self.settings.tts_speed,
                response_format="mp3",
            )

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Stream the response to file
            with open(output_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

            logger.info(f"TTS audio saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise TTSError(f"Failed to generate TTS: {e}") from e

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def transcribe_audio(self, audio_path: Path) -> Transcription:
        """Transcribe audio with word-level timestamps using Whisper.

        Args:
            audio_path: Path to the audio file to transcribe.

        Returns:
            Transcription object with word-level timestamps.

        Raises:
            TranscriptionError: If transcription fails.
        """
        logger.info(f"Transcribing audio: {audio_path}")

        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model=self.settings.whisper_model,
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )

            # Parse the response
            response_dict = response.model_dump()

            # Handle the response structure
            words = []
            if "words" in response_dict:
                for word_data in response_dict["words"]:
                    words.append(
                        WordTimestamp(
                            word=word_data["word"],
                            start=word_data["start"],
                            end=word_data["end"],
                        )
                    )

            # Calculate total duration
            duration = words[-1].end if words else response_dict.get("duration", 0.0)

            transcription = Transcription(
                text=response_dict.get("text", ""),
                words=words,
                duration=duration,
            )

            logger.info(
                f"Transcription complete: {len(transcription.words)} words, "
                f"{transcription.duration:.2f}s duration"
            )
            return transcription

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Failed to transcribe audio: {e}") from e

    async def validate_video_frame(
        self,
        frame_path: Path,
        keyword: str,
        context: str | None = None,
    ) -> tuple[bool, float, str]:
        """Validate that a video frame matches the expected keyword using GPT-4 Vision.

        Args:
            frame_path: Path to the frame image file.
            keyword: The keyword/concept the frame should represent.
            context: Optional additional context about what we're looking for.

        Returns:
            Tuple of (is_valid, confidence_score, explanation).

        Raises:
            VisionError: If vision analysis fails.
        """
        logger.info(f"Validating frame for keyword: '{keyword}'")

        if not frame_path.exists():
            raise VisionError(f"Frame file not found: {frame_path}")

        try:
            # Read and encode the image
            with open(frame_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Determine the media type
            suffix = frame_path.suffix.lower()
            media_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "image/jpeg")

            # Build the prompt
            context_text = f" Context: {context}" if context else ""
            prompt = f"""Analyze this video frame and determine if it matches the keyword/concept: "{keyword}".{context_text}

Respond with a JSON object containing:
- "matches": boolean (true if the frame reasonably matches the keyword concept)
- "confidence": float between 0 and 1 (how confident you are in the match)
- "explanation": string (brief explanation of your assessment)

Consider:
1. Does the visual content relate to the keyword concept?
2. Would this footage be appropriate for a video about this topic?
3. Is the content high quality and visually appealing?

Be reasonably flexible - the footage doesn't need to be a perfect literal match, just conceptually appropriate for the keyword."""

            response = await self.client.chat.completions.create(
                model=self.settings.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}",
                                    "detail": "low",  # Use low detail for faster processing
                                },
                            },
                        ],
                    }
                ],
                max_tokens=self.settings.vision_max_tokens,
                response_format={"type": "json_object"},
            )

            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise VisionError("Empty response from vision model")

            import json

            result = json.loads(content)

            is_valid = result.get("matches", False)
            confidence = float(result.get("confidence", 0.0))
            explanation = result.get("explanation", "No explanation provided")

            logger.info(
                f"Validation result for '{keyword}': valid={is_valid}, "
                f"confidence={confidence:.2f}, reason={explanation[:50]}..."
            )

            return is_valid, confidence, explanation

        except Exception as e:
            logger.error(f"Vision validation failed: {e}")
            raise VisionError(f"Failed to validate video frame: {e}") from e

    async def validate_video_frames_batch(
        self,
        frame_keyword_pairs: list[tuple[Path, str]],
        context: str | None = None,
    ) -> list[tuple[bool, float, str]]:
        """Validate multiple video frames in parallel.

        Args:
            frame_keyword_pairs: List of (frame_path, keyword) tuples.
            context: Optional context for all validations.

        Returns:
            List of validation results in the same order.
        """
        tasks = [
            self.validate_video_frame(frame_path, keyword, context)
            for frame_path, keyword in frame_keyword_pairs
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def generate_alternative_keyword(
        self,
        original_keyword: str,
        failed_keywords: list[str] | None = None,
        context: str | None = None,
    ) -> str:
        """Generate an alternative search keyword when original fails to find stock footage.

        Args:
            original_keyword: The original keyword that failed.
            failed_keywords: List of previously failed alternative keywords to avoid.
            context: Optional context about what the video is for.

        Returns:
            An alternative search keyword to try.
        """
        logger.info(f"Generating alternative keyword for: '{original_keyword}'")

        failed_list = failed_keywords or []
        failed_text = (
            "\n\nPreviously tried keywords that also failed:\n- " + "\n- ".join(failed_list)
            if failed_list
            else ""
        )
        context_text = f"\n\nContext: {context}" if context else ""

        prompt = f"""The stock footage search for "{original_keyword}" failed to find suitable videos on Pexels.

Generate ONE alternative search keyword that:
1. Captures a similar visual concept but is more generic/common
2. Is likely to find stock video footage
3. Uses simple, common terms that stock video sites would have
4. Is different from the original keyword{failed_text}{context_text}

Respond with ONLY the alternative keyword, nothing else. Keep it short (2-5 words max)."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for this task
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=50,
                temperature=0.8,  # Allow some creativity
            )

            alternative = response.choices[0].message.content
            if alternative:
                alternative = alternative.strip().strip('"\'')
                logger.info(f"Generated alternative keyword: '{alternative}'")
                return alternative
            else:
                # Fallback: simplify the original keyword
                words = original_keyword.split()
                return " ".join(words[:2]) if len(words) > 2 else original_keyword

        except Exception as e:
            logger.warning(f"Failed to generate alternative keyword: {e}")
            # Fallback: simplify the original keyword
            words = original_keyword.split()
            return " ".join(words[:2]) if len(words) > 2 else original_keyword
