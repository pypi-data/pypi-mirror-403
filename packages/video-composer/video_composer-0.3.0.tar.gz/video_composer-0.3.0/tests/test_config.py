"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from video_composer.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading settings from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("PEXELS_API_KEY", "test-pexels-key")
        monkeypatch.setenv("VIDEO_WIDTH", "720")
        monkeypatch.setenv("VIDEO_HEIGHT", "1280")
        monkeypatch.setenv("TTS_VOICE", "echo")

        settings = Settings()

        assert settings.openai_api_key == "test-openai-key"
        assert settings.pexels_api_key == "test-pexels-key"
        assert settings.video_width == 720
        assert settings.video_height == 1280
        assert settings.tts_voice == "echo"

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default setting values."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PEXELS_API_KEY", "test-key")

        settings = Settings()

        # Video defaults
        assert settings.video_width == 1080
        assert settings.video_height == 1920
        assert settings.video_fps == 30

        # TTS defaults
        assert settings.tts_model == "tts-1-hd"
        assert settings.tts_voice == "nova"
        assert settings.tts_speed == 1.0

        # Processing defaults
        assert settings.max_retries == 3

    def test_ensure_directories(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test directory creation."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PEXELS_API_KEY", "test-key")

        temp_dir = tmp_path / "temp"
        output_dir = tmp_path / "output"

        settings = Settings(
            openai_api_key="test-key",
            pexels_api_key="test-key",
            temp_dir=temp_dir,
            output_dir=output_dir,
        )

        assert not temp_dir.exists()
        assert not output_dir.exists()

        settings.ensure_directories()

        assert temp_dir.exists()
        assert output_dir.exists()

    def test_path_conversion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test path string to Path conversion."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PEXELS_API_KEY", "test-key")
        monkeypatch.setenv("TEMP_DIR", "/custom/temp")
        monkeypatch.setenv("OUTPUT_DIR", "/custom/output")

        settings = Settings()

        assert isinstance(settings.temp_dir, Path)
        assert isinstance(settings.output_dir, Path)
        assert str(settings.temp_dir) == "/custom/temp"
        assert str(settings.output_dir) == "/custom/output"

    def test_tts_speed_validation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test TTS speed bounds validation."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PEXELS_API_KEY", "test-key")

        # Valid speed
        settings = Settings(
            openai_api_key="test-key",
            pexels_api_key="test-key",
            tts_speed=2.0,
        )
        assert settings.tts_speed == 2.0

        # Invalid speed - too low
        with pytest.raises(ValueError):
            Settings(
                openai_api_key="test-key",
                pexels_api_key="test-key",
                tts_speed=0.1,  # Below minimum of 0.25
            )

        # Invalid speed - too high
        with pytest.raises(ValueError):
            Settings(
                openai_api_key="test-key",
                pexels_api_key="test-key",
                tts_speed=5.0,  # Above maximum of 4.0
            )

    def test_validation_frame_position_bounds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation frame position bounds."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PEXELS_API_KEY", "test-key")

        # Valid position
        settings = Settings(
            openai_api_key="test-key",
            pexels_api_key="test-key",
            validation_frame_position=0.5,
        )
        assert settings.validation_frame_position == 0.5

        # Invalid - below 0
        with pytest.raises(ValueError):
            Settings(
                openai_api_key="test-key",
                pexels_api_key="test-key",
                validation_frame_position=-0.1,
            )

        # Invalid - above 1
        with pytest.raises(ValueError):
            Settings(
                openai_api_key="test-key",
                pexels_api_key="test-key",
                validation_frame_position=1.5,
            )
