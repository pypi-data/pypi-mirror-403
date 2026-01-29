"""YAML-based video configuration models."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SubtitleConfig(BaseModel):
    """Subtitle styling configuration."""

    enabled: bool = Field(default=True, description="Enable subtitle generation")
    font: str = Field(default="Arial", description="Font family name")
    font_size: int = Field(default=48, ge=12, le=120)
    primary_color: str = Field(default="#FFFFFF", description="Main text color (hex)")
    highlight_color: str = Field(default="#FFFF00", description="Karaoke highlight color (hex)")
    outline_color: str = Field(default="#000000", description="Text outline color (hex)")
    outline_width: int = Field(default=3, ge=0, le=10)
    shadow_depth: int = Field(default=2, ge=0, le=10)
    position: Literal["top", "center", "bottom"] = Field(default="bottom")
    margin: int = Field(default=150, ge=0, le=500)
    words_per_line: int = Field(default=4, ge=1, le=10)


class VoiceConfig(BaseModel):
    """Voice/TTS configuration."""

    model: str = Field(default="tts-1-hd")
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(default="nova")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class VideoSettings(BaseModel):
    """Video output settings."""

    width: int = Field(default=1080)
    height: int = Field(default=1920)
    fps: int = Field(default=30, ge=24, le=60)
    codec: str = Field(default="libx264")
    quality: Literal["low", "medium", "high", "ultra"] = Field(default="high")


class VideoProject(BaseModel):
    """Single video project configuration."""

    name: str = Field(..., description="Unique name for this video")
    script: str = Field(..., min_length=10, description="The marketing script text")
    keywords: list[str] = Field(..., min_length=1, description="Keywords for stock footage")

    # Optional overrides
    voice: VoiceConfig | None = None
    subtitles: SubtitleConfig | None = None
    output_filename: str | None = Field(None, description="Custom output filename")
    context: str | None = Field(None, description="Additional context for AI validation")

    # Scheduling (for future use)
    schedule: str | None = Field(None, description="Cron expression for scheduling")
    platforms: list[str] | None = Field(
        None, description="Target platforms: tiktok, youtube, instagram"
    )

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("At least 1 keyword is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 keywords allowed")
        return [k.strip() for k in v if k.strip()]


class BatchConfig(BaseModel):
    """Batch video generation configuration from YAML."""

    version: str = Field(default="1.0", description="Config schema version")

    # Global defaults
    defaults: dict = Field(default_factory=dict, description="Default settings for all videos")
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    subtitles: SubtitleConfig = Field(default_factory=SubtitleConfig)
    video: VideoSettings = Field(default_factory=VideoSettings)

    # Video projects
    videos: list[VideoProject] = Field(..., min_length=1, description="List of videos to generate")

    # Output settings
    output_dir: str = Field(default="./output", description="Output directory for videos")
    keep_temp: bool = Field(default=False, description="Keep temporary files")

    @field_validator("videos")
    @classmethod
    def validate_unique_names(cls, v: list[VideoProject]) -> list[VideoProject]:
        names = [video.name for video in v]
        if len(names) != len(set(names)):
            raise ValueError("Video names must be unique")
        return v


class SingleVideoConfig(BaseModel):
    """Single video configuration from YAML (simpler format)."""

    script: str = Field(..., min_length=10)
    keywords: list[str] = Field(..., min_length=1)

    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    subtitles: SubtitleConfig = Field(default_factory=SubtitleConfig)
    video: VideoSettings = Field(default_factory=VideoSettings)

    output_filename: str | None = None
    output_dir: str = Field(default="./output")
    context: str | None = None
    keep_temp: bool = Field(default=False)
