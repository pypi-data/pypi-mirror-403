"""Data models for the video composer."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class WordTimestamp:
    """A single word with its timing information."""

    word: str
    start: float  # Start time in seconds
    end: float  # End time in seconds

    @property
    def duration(self) -> float:
        """Duration of the word in seconds."""
        return self.end - self.start


@dataclass
class Transcription:
    """Full transcription with word-level timestamps."""

    text: str
    words: list[WordTimestamp]
    duration: float  # Total duration in seconds

    @classmethod
    def from_whisper_response(cls, response: dict) -> "Transcription":
        """Create a Transcription from Whisper API response."""
        words = []
        for word_data in response.get("words", []):
            words.append(
                WordTimestamp(
                    word=word_data["word"],
                    start=word_data["start"],
                    end=word_data["end"],
                )
            )

        # Calculate total duration from last word's end time
        duration = words[-1].end if words else 0.0

        return cls(
            text=response.get("text", ""),
            words=words,
            duration=duration,
        )


@dataclass
class StockVideo:
    """Stock video metadata (provider-agnostic)."""

    id: int
    width: int
    height: int
    duration: int  # Duration in seconds
    url: str  # Page URL
    video_files: list["StockVideoFile"]
    video_pictures: list[str]  # Preview image URLs
    provider: str = "unknown"  # e.g., "pexels", "pixabay"

    def get_best_file(
        self,
        target_width: int = 1080,
        target_height: int = 1920,
        quality: Literal["hd", "sd"] = "hd",
    ) -> "StockVideoFile | None":
        """Get the best video file matching criteria."""
        suitable_files = [
            f
            for f in self.video_files
            if f.width >= target_width and f.height >= target_height and f.quality == quality
        ]

        if not suitable_files:
            # Fall back to any HD file
            suitable_files = [f for f in self.video_files if f.quality == quality]

        if not suitable_files:
            # Fall back to any file
            suitable_files = self.video_files

        if not suitable_files:
            return None

        # Sort by resolution (prefer closest to target)
        suitable_files.sort(key=lambda f: abs(f.width - target_width) + abs(f.height - target_height))
        return suitable_files[0]


@dataclass
class StockVideoFile:
    """A specific video file from a stock provider."""

    id: int
    quality: str
    file_type: str
    width: int
    height: int
    link: str


@dataclass
class StockFootage:
    """Validated stock footage ready for use."""

    keyword: str
    video: StockVideo
    local_path: Path
    validation_score: float  # 0-1 confidence score
    is_validated: bool


@dataclass
class VideoSegment:
    """A segment of the final video."""

    footage: StockFootage
    start_time: float
    end_time: float
    words: list[WordTimestamp]

    @property
    def duration(self) -> float:
        """Duration of this segment."""
        return self.end_time - self.start_time


@dataclass
class VideoProject:
    """Complete video project configuration."""

    script: str
    keywords: list[str]
    audio_path: Path | None = None
    transcription: Transcription | None = None
    segments: list[VideoSegment] = field(default_factory=list)
    output_path: Path | None = None

    @property
    def duration(self) -> float:
        """Total video duration based on transcription."""
        if self.transcription:
            return self.transcription.duration
        return 0.0


@dataclass
class CompositionResult:
    """Result of video composition."""

    success: bool
    output_path: Path | None
    duration: float
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
