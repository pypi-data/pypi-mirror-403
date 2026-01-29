"""
Video Composer - Social video automation tool for generating vertical short-form marketing videos.

This package provides tools for:
- Generating TTS audio using OpenAI's tts-1-hd
- Transcribing audio with word-level timestamps using Whisper
- Fetching and validating stock footage from Pexels or Pixabay
- Generating ASS subtitles with karaoke-style animation
- Composing final videos in 9:16 aspect ratio for TikTok/Shorts
"""

from video_composer.composer import VideoComposer
from video_composer.config import Settings

__version__ = "0.4.0"
__all__ = ["VideoComposer", "Settings"]
