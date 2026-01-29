"""Tests for data models."""

import pytest

from video_composer.models import (
    CompositionResult,
    StockFootage,
    StockVideo,
    StockVideoFile,
    Transcription,
    VideoProject,
    VideoSegment,
    WordTimestamp,
)


class TestWordTimestamp:
    """Tests for WordTimestamp model."""

    def test_duration(self) -> None:
        """Test duration calculation."""
        word = WordTimestamp(word="hello", start=1.0, end=2.5)
        assert word.duration == 1.5

    def test_zero_duration(self) -> None:
        """Test zero duration word."""
        word = WordTimestamp(word="a", start=1.0, end=1.0)
        assert word.duration == 0.0


class TestTranscription:
    """Tests for Transcription model."""

    def test_from_whisper_response(self) -> None:
        """Test creating transcription from Whisper response."""
        response = {
            "text": "Hello world",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.6, "end": 1.0},
            ],
        }

        transcription = Transcription.from_whisper_response(response)

        assert transcription.text == "Hello world"
        assert len(transcription.words) == 2
        assert transcription.words[0].word == "Hello"
        assert transcription.duration == 1.0

    def test_empty_response(self) -> None:
        """Test handling empty Whisper response."""
        response = {"text": "", "words": []}
        transcription = Transcription.from_whisper_response(response)

        assert transcription.text == ""
        assert len(transcription.words) == 0
        assert transcription.duration == 0.0


class TestStockVideo:
    """Tests for StockVideo model."""

    def test_get_best_file_exact_match(self) -> None:
        """Test getting best file with exact match."""
        video = StockVideo(
            id=1,
            width=1920,
            height=1080,
            duration=10,
            url="https://pexels.com/1",
            video_files=[
                StockVideoFile(
                    id=1,
                    quality="hd",
                    file_type="video/mp4",
                    width=1080,
                    height=1920,
                    link="https://example.com/hd.mp4",
                ),
            ],
            video_pictures=[],
            provider="pexels",
        )

        best = video.get_best_file(target_width=1080, target_height=1920)
        assert best is not None
        assert best.quality == "hd"
        assert best.width == 1080

    def test_get_best_file_fallback(self) -> None:
        """Test fallback when no exact match."""
        video = StockVideo(
            id=1,
            width=1920,
            height=1080,
            duration=10,
            url="https://pexels.com/1",
            video_files=[
                StockVideoFile(
                    id=1,
                    quality="sd",
                    file_type="video/mp4",
                    width=640,
                    height=480,
                    link="https://example.com/sd.mp4",
                ),
            ],
            video_pictures=[],
            provider="pexels",
        )

        # Should fall back to SD when HD not available
        best = video.get_best_file(target_width=1080, target_height=1920, quality="hd")
        assert best is not None

    def test_get_best_file_empty(self) -> None:
        """Test with no video files."""
        video = StockVideo(
            id=1,
            width=1920,
            height=1080,
            duration=10,
            url="https://pexels.com/1",
            video_files=[],
            video_pictures=[],
            provider="pexels",
        )

        best = video.get_best_file()
        assert best is None


class TestVideoSegment:
    """Tests for VideoSegment model."""

    def test_duration(self, sample_stock_footage: StockFootage) -> None:
        """Test segment duration calculation."""
        segment = VideoSegment(
            footage=sample_stock_footage,
            start_time=1.0,
            end_time=5.5,
            words=[],
        )
        assert segment.duration == 4.5


class TestVideoProject:
    """Tests for VideoProject model."""

    def test_duration_with_transcription(
        self, sample_transcription: Transcription
    ) -> None:
        """Test project duration from transcription."""
        project = VideoProject(
            script="Test script",
            keywords=["test"],
            transcription=sample_transcription,
        )
        assert project.duration == sample_transcription.duration

    def test_duration_without_transcription(self) -> None:
        """Test project duration without transcription."""
        project = VideoProject(
            script="Test script",
            keywords=["test"],
        )
        assert project.duration == 0.0


class TestCompositionResult:
    """Tests for CompositionResult model."""

    def test_success_result(self, temp_dir: "Path") -> None:
        """Test successful composition result."""
        from pathlib import Path

        result = CompositionResult(
            success=True,
            output_path=temp_dir / "output.mp4",
            duration=30.5,
        )

        assert result.success is True
        assert result.output_path is not None
        assert result.duration == 30.5
        assert result.error is None
        assert result.warnings == []

    def test_failure_result(self) -> None:
        """Test failed composition result."""
        result = CompositionResult(
            success=False,
            output_path=None,
            duration=0.0,
            error="Something went wrong",
            warnings=["Warning 1", "Warning 2"],
        )

        assert result.success is False
        assert result.output_path is None
        assert result.error == "Something went wrong"
        assert len(result.warnings) == 2


# Import at the end
from pathlib import Path
