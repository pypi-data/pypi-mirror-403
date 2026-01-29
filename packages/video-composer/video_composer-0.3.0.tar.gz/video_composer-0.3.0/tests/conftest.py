"""Pytest configuration and fixtures."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from video_composer.config import Settings
from video_composer.models import (
    StockFootage,
    StockVideo,
    StockVideoFile,
    Transcription,
    WordTimestamp,
)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def mock_settings(temp_dir: Path) -> Settings:
    """Create mock settings for testing."""
    # Set environment variables for testing
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["PEXELS_API_KEY"] = "test-pexels-key"

    settings = Settings(
        openai_api_key="test-openai-key",
        pexels_api_key="test-pexels-key",
        temp_dir=temp_dir / "temp",
        output_dir=temp_dir / "output",
    )
    settings.ensure_directories()
    return settings


@pytest.fixture
def sample_transcription() -> Transcription:
    """Create a sample transcription for testing."""
    words = [
        WordTimestamp(word="Welcome", start=0.0, end=0.5),
        WordTimestamp(word="to", start=0.5, end=0.6),
        WordTimestamp(word="the", start=0.6, end=0.7),
        WordTimestamp(word="future", start=0.7, end=1.0),
        WordTimestamp(word="of", start=1.0, end=1.1),
        WordTimestamp(word="technology.", start=1.1, end=1.8),
        WordTimestamp(word="Innovation", start=2.0, end=2.5),
        WordTimestamp(word="drives", start=2.5, end=2.8),
        WordTimestamp(word="success.", start=2.8, end=3.5),
    ]
    return Transcription(
        text="Welcome to the future of technology. Innovation drives success.",
        words=words,
        duration=3.5,
    )


@pytest.fixture
def sample_stock_video() -> StockVideo:
    """Create a sample stock video for testing."""
    return StockVideo(
        id=12345,
        width=1920,
        height=1080,
        duration=10,
        url="https://www.pexels.com/video/12345/",
        video_files=[
            StockVideoFile(
                id=1,
                quality="hd",
                file_type="video/mp4",
                width=1920,
                height=1080,
                link="https://videos.pexels.com/12345/hd.mp4",
            ),
            StockVideoFile(
                id=2,
                quality="sd",
                file_type="video/mp4",
                width=960,
                height=540,
                link="https://videos.pexels.com/12345/sd.mp4",
            ),
        ],
        video_pictures=["https://images.pexels.com/12345/preview.jpg"],
        provider="pexels",
    )


@pytest.fixture
def sample_stock_footage(
    sample_stock_video: StockVideo,
    temp_dir: Path,
) -> StockFootage:
    """Create sample stock footage for testing."""
    # Create a dummy video file
    video_path = temp_dir / "test_video.mp4"
    video_path.touch()

    return StockFootage(
        keyword="technology",
        video=sample_stock_video,
        local_path=video_path,
        validation_score=0.85,
        is_validated=True,
    )


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Create a mock OpenAI client."""
    client = MagicMock()

    # Mock TTS
    client.audio.speech.create = AsyncMock(
        return_value=MagicMock(
            iter_bytes=MagicMock(return_value=[b"fake audio data"])
        )
    )

    # Mock Whisper transcription
    client.audio.transcriptions.create = AsyncMock(
        return_value=MagicMock(
            model_dump=MagicMock(
                return_value={
                    "text": "Test transcription",
                    "words": [
                        {"word": "Test", "start": 0.0, "end": 0.5},
                        {"word": "transcription", "start": 0.5, "end": 1.2},
                    ],
                    "duration": 1.2,
                }
            )
        )
    )

    # Mock Vision
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"matches": true, "confidence": 0.9, "explanation": "Good match"}'
                    )
                )
            ]
        )
    )

    return client
