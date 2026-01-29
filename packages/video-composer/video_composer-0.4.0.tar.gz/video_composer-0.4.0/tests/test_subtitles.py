"""Tests for subtitle generation."""

from pathlib import Path

import pytest

from video_composer.models import Transcription, WordTimestamp
from video_composer.utils.subtitles import SubtitleGenerator, SubtitleStyle


class TestSubtitleStyle:
    """Tests for SubtitleStyle class."""

    def test_default_style(self) -> None:
        """Test default style creation."""
        style = SubtitleStyle()
        assert style.name == "Default"
        assert style.font_name == "Arial"
        assert style.font_size == 48

    def test_to_ass_line(self) -> None:
        """Test ASS line generation."""
        style = SubtitleStyle(name="Custom", font_name="Roboto", font_size=36)
        line = style.to_ass_line()

        assert line.startswith("Style: Custom,Roboto,36,")
        assert "&H00FFFFFF" in line  # Primary color

    def test_custom_style(self) -> None:
        """Test custom style properties."""
        style = SubtitleStyle(
            name="Bold",
            font_name="Impact",
            font_size=64,
            bold=True,
            outline=5,
        )
        assert style.name == "Bold"
        assert style.font_name == "Impact"
        assert style.font_size == 64
        assert style.bold is True
        assert style.outline == 5


class TestSubtitleGenerator:
    """Tests for SubtitleGenerator class."""

    def test_format_time(self) -> None:
        """Test time formatting for ASS."""
        # Test basic time
        result = SubtitleGenerator._format_time(65.5)
        assert result == "0:01:05.50"

        # Test zero
        result = SubtitleGenerator._format_time(0.0)
        assert result == "0:00:00.00"

        # Test hours
        result = SubtitleGenerator._format_time(3723.25)
        assert result == "1:02:03.25"

    def test_format_srt_time(self) -> None:
        """Test time formatting for SRT."""
        result = SubtitleGenerator._format_srt_time(65.5)
        assert result == "00:01:05,500"

        result = SubtitleGenerator._format_srt_time(0.0)
        assert result == "00:00:00,000"

    def test_escape_text(self) -> None:
        """Test text escaping for ASS."""
        # Test newline
        result = SubtitleGenerator._escape_text("Hello\nWorld")
        assert result == "Hello\\NWorld"

        # Test normal text
        result = SubtitleGenerator._escape_text("Normal text")
        assert result == "Normal text"

    def test_generate_subtitles(
        self,
        mock_settings: "Settings",
        sample_transcription: Transcription,
        temp_dir: Path,
    ) -> None:
        """Test ASS subtitle generation."""
        generator = SubtitleGenerator(mock_settings)
        output_path = temp_dir / "test.ass"

        result = generator.generate_subtitles(
            sample_transcription,
            output_path,
            words_per_line=4,
        )

        assert result.exists()

        # Read and verify content
        content = result.read_text()
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "Dialogue:" in content

    def test_generate_simple_subtitles(
        self,
        mock_settings: "Settings",
        sample_transcription: Transcription,
        temp_dir: Path,
    ) -> None:
        """Test SRT subtitle generation."""
        generator = SubtitleGenerator(mock_settings)
        output_path = temp_dir / "test.srt"

        result = generator.generate_simple_subtitles(
            sample_transcription,
            output_path,
            words_per_line=4,
        )

        assert result.exists()

        # Read and verify content
        content = result.read_text()
        assert "1\n" in content  # First subtitle index
        assert "-->" in content  # Time separator

    def test_karaoke_timing(
        self,
        mock_settings: "Settings",
        temp_dir: Path,
    ) -> None:
        """Test karaoke timing in generated subtitles."""
        # Create transcription with specific timing
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.5),
            WordTimestamp(word="World", start=0.6, end=1.0),
        ]
        transcription = Transcription(
            text="Hello World",
            words=words,
            duration=1.0,
        )

        generator = SubtitleGenerator(mock_settings)
        output_path = temp_dir / "karaoke.ass"

        result = generator.generate_subtitles(
            transcription,
            output_path,
            words_per_line=10,
        )

        content = result.read_text()

        # Check for karaoke tags (\\kf = karaoke fill)
        assert "\\kf" in content


# Import at the end to avoid issues
from video_composer.config import Settings
