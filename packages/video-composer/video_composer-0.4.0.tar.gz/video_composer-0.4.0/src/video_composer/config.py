"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = Field(..., description="OpenAI API key for TTS, Whisper, and Vision")
    pexels_api_key: str = Field(default="", description="Pexels API key for stock footage")
    pixabay_api_key: str = Field(default="", description="Pixabay API key for stock footage")

    # Stock Provider Settings
    stock_provider: Literal["pexels", "pixabay"] = Field(
        default="pexels", description="Stock footage provider to use"
    )

    # Video Settings
    video_width: int = Field(default=1080, description="Output video width in pixels")
    video_height: int = Field(default=1920, description="Output video height in pixels (9:16)")
    video_fps: int = Field(default=30, description="Output video frames per second")
    video_codec: str = Field(default="libx264", description="Video codec for encoding")
    audio_codec: str = Field(default="aac", description="Audio codec for encoding")

    # TTS Settings
    tts_model: Literal["tts-1", "tts-1-hd"] = Field(
        default="tts-1-hd", description="OpenAI TTS model"
    )
    tts_voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(
        default="nova", description="TTS voice selection"
    )
    tts_speed: float = Field(default=1.0, ge=0.25, le=4.0, description="TTS speech speed")

    # Whisper Settings
    whisper_model: Literal["whisper-1"] = Field(default="whisper-1", description="Whisper model")

    # Vision Settings
    vision_model: str = Field(default="gpt-4o", description="GPT-4 Vision model for validation")
    vision_max_tokens: int = Field(default=300, description="Max tokens for vision response")

    # Pexels Settings
    pexels_videos_per_query: int = Field(
        default=10, description="Number of videos to fetch per keyword"
    )
    pexels_min_duration: int = Field(default=5, description="Minimum video duration in seconds")
    pexels_orientation: Literal["landscape", "portrait", "square"] = Field(
        default="portrait", description="Video orientation preference"
    )

    # Pixabay Settings
    pixabay_videos_per_query: int = Field(
        default=10, description="Number of videos to fetch per keyword from Pixabay"
    )
    pixabay_min_duration: int = Field(default=5, description="Minimum video duration in seconds")

    # Subtitle Settings
    subtitle_font: str = Field(default="Arial", description="Font for subtitles")
    subtitle_font_size: int = Field(default=48, description="Font size for subtitles")
    subtitle_primary_color: str = Field(
        default="&H00FFFFFF", description="Primary subtitle color (ASS format)"
    )
    subtitle_highlight_color: str = Field(
        default="&H0000FFFF", description="Highlight color for karaoke effect (ASS format)"
    )
    subtitle_outline_color: str = Field(
        default="&H00000000", description="Outline color (ASS format)"
    )
    subtitle_outline_width: int = Field(default=3, description="Outline width in pixels")
    subtitle_shadow_depth: int = Field(default=2, description="Shadow depth in pixels")
    subtitle_margin_bottom: int = Field(
        default=150, description="Bottom margin for subtitles in pixels"
    )
    subtitle_position: Literal["top", "center", "bottom"] = Field(
        default="bottom", description="Subtitle vertical position"
    )
    subtitle_words_per_line: int = Field(
        default=4, ge=1, le=10, description="Maximum words per subtitle line"
    )
    subtitles_enabled: bool = Field(default=True, description="Enable subtitle generation")

    # Processing Settings
    temp_dir: Path = Field(default=Path("./temp"), description="Temporary directory for assets")
    output_dir: Path = Field(default=Path("./output"), description="Output directory for videos")
    max_retries: int = Field(default=5, description="Maximum retries for API calls")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    validation_frame_position: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Position (0-1) to extract frame for validation",
    )

    @field_validator("temp_dir", "output_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Convert string to Path if needed."""
        return Path(v) if isinstance(v, str) else v

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance (lazy loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
        _settings.ensure_directories()
    return _settings
