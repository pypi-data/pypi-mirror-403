"""ASS subtitle generation with karaoke-style word-by-word animation."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from video_composer.config import Settings
    from video_composer.models import Transcription, WordTimestamp

logger = logging.getLogger(__name__)


def normalize_ass_color(color: str) -> str:
    """Normalize color to ASS AABBGGRR format.

    Accepts hex (#RRGGBB) or ASS colors (&H00BBGGRR).
    """
    if not color:
        return color

    stripped = color.strip()
    if stripped.startswith("&H"):
        return stripped.upper()

    if stripped.startswith("#") and len(stripped) == 7:
        r = stripped[1:3]
        g = stripped[3:5]
        b = stripped[5:7]
        return f"&H00{b}{g}{r}".upper()

    return stripped


def resolve_alignment(position: str) -> int:
    """Map position to ASS alignment values."""
    position_map = {
        "top": 8,
        "center": 5,
        "bottom": 2,
    }
    return position_map.get(position, 2)


@dataclass
class SubtitleStyle:
    """ASS subtitle style configuration."""

    name: str = "Default"
    font_name: str = "Arial"
    font_size: int = 48
    primary_color: str = "&H00FFFFFF"  # White (AABBGGRR format)
    secondary_color: str = "&H000000FF"  # Red
    outline_color: str = "&H00000000"  # Black
    back_color: str = "&H80000000"  # Semi-transparent black
    bold: bool = True
    italic: bool = False
    underline: bool = False
    strike_out: bool = False
    scale_x: int = 100
    scale_y: int = 100
    spacing: int = 0
    angle: float = 0
    border_style: int = 1  # 1 = outline + shadow
    outline: int = 3
    shadow: int = 2
    alignment: int = 2  # 2 = bottom center
    margin_l: int = 20
    margin_r: int = 20
    margin_v: int = 150
    encoding: int = 1

    def to_ass_line(self) -> str:
        """Convert style to ASS format line."""
        return (
            f"Style: {self.name},{self.font_name},{self.font_size},"
            f"{self.primary_color},{self.secondary_color},"
            f"{self.outline_color},{self.back_color},"
            f"{int(self.bold)},{int(self.italic)},{int(self.underline)},{int(self.strike_out)},"
            f"{self.scale_x},{self.scale_y},{self.spacing},{self.angle},"
            f"{self.border_style},{self.outline},{self.shadow},"
            f"{self.alignment},{self.margin_l},{self.margin_r},{self.margin_v},{self.encoding}"
        )


class SubtitleGenerator:
    """Generator for ASS subtitles with karaoke-style word animation."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the subtitle generator.

        Args:
            settings: Application settings for subtitle styling.
        """
        self.settings = settings
        base_color = normalize_ass_color(settings.subtitle_primary_color)
        highlight_color = normalize_ass_color(settings.subtitle_highlight_color)
        outline_color = normalize_ass_color(settings.subtitle_outline_color)

        self.default_style = SubtitleStyle(
            font_name=settings.subtitle_font,
            font_size=settings.subtitle_font_size,
            primary_color=highlight_color,
            secondary_color=base_color,
            outline_color=outline_color,
            outline=settings.subtitle_outline_width,
            shadow=settings.subtitle_shadow_depth,
            alignment=resolve_alignment(settings.subtitle_position),
            margin_v=settings.subtitle_margin_bottom,
        )
        self.highlight_color = highlight_color

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc).

        Args:
            seconds: Time in seconds.

        Returns:
            ASS formatted time string.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    @staticmethod
    def _escape_text(text: str) -> str:
        """Escape special characters for ASS format.

        Args:
            text: Raw text to escape.

        Returns:
            Escaped text safe for ASS.
        """
        # Replace newlines with ASS line break
        text = text.replace("\n", "\\N")
        # Escape curly braces that aren't ASS tags
        # (We need to be careful not to escape our own tags)
        return text

    def _generate_header(self, video_width: int, video_height: int) -> str:
        """Generate ASS file header.

        Args:
            video_width: Video width in pixels.
            video_height: Video height in pixels.

        Returns:
            ASS header string.
        """
        return f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{self.default_style.to_ass_line()}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def _generate_karaoke_line(
        self,
        words: list["WordTimestamp"],
        line_start: float,
        line_end: float,
    ) -> str:
        """Generate a single subtitle line with karaoke effect.

        The karaoke effect highlights each word as it's spoken using
        the \\k tag which specifies duration in centiseconds.

        Args:
            words: List of words with timestamps for this line.
            line_start: Start time of the line.
            line_end: End time of the line.

        Returns:
            ASS dialogue line with karaoke tags.
        """
        if not words:
            return ""

        # Build the karaoke text
        karaoke_parts: list[str] = []

        for i, word in enumerate(words):
            # Calculate duration in centiseconds
            duration_cs = int((word.end - word.start) * 100)

            # Use \kf for smooth fill effect (karaoke fill)
            # The color change happens gradually over the duration
            word_text = self._escape_text(word.word.strip())

            if i == 0:
                # First word - add any leading silence
                lead_in = int((word.start - line_start) * 100)
                if lead_in > 0:
                    karaoke_parts.append(f"{{\\k{lead_in}}}")

            # Add the karaoke tag with highlight color transition
            # \kf = karaoke fill (smooth highlight)
            # We use \1c for primary color change during karaoke
            karaoke_parts.append(f"{{\\kf{duration_cs}}}{word_text}")

            # Add space after word (except for last word)
            if i < len(words) - 1:
                # Calculate gap to next word
                gap = words[i + 1].start - word.end
                if gap > 0.05:  # Only add visible gap if significant
                    gap_cs = int(gap * 100)
                    karaoke_parts.append(f"{{\\k{gap_cs}}} ")
                else:
                    karaoke_parts.append(" ")

        karaoke_text = "".join(karaoke_parts)

        # Format the dialogue line
        start_time = self._format_time(line_start)
        end_time = self._format_time(line_end)

        return f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}"

    def generate_subtitles(
        self,
        transcription: "Transcription",
        output_path: Path,
        words_per_line: int = 4,
        video_width: int | None = None,
        video_height: int | None = None,
    ) -> Path:
        """Generate ASS subtitle file with karaoke-style animation.

        Args:
            transcription: Transcription with word-level timestamps.
            output_path: Path to save the ASS file.
            words_per_line: Maximum words per subtitle line.
            video_width: Video width (defaults to settings).
            video_height: Video height (defaults to settings).

        Returns:
            Path to the generated subtitle file.
        """
        if video_width is None:
            video_width = self.settings.video_width
        if video_height is None:
            video_height = self.settings.video_height

        logger.info(
            f"Generating subtitles: {len(transcription.words)} words, {words_per_line} words/line"
        )

        # Build the ASS content
        lines: list[str] = [self._generate_header(video_width, video_height)]

        # Group words into lines
        current_line_words: list[WordTimestamp] = []

        for word in transcription.words:
            current_line_words.append(word)

            # Check if we should end this line
            should_end_line = len(
                current_line_words
            ) >= words_per_line or word.word.rstrip().endswith((".", "!", "?", ",", ";", ":"))

            if should_end_line and current_line_words:
                line_start = current_line_words[0].start
                line_end = current_line_words[-1].end

                # Add a small buffer at the end for readability
                line_end = min(line_end + 0.1, transcription.duration)

                dialogue = self._generate_karaoke_line(
                    current_line_words,
                    line_start,
                    line_end,
                )
                lines.append(dialogue)
                current_line_words = []

        # Handle any remaining words
        if current_line_words:
            line_start = current_line_words[0].start
            line_end = current_line_words[-1].end + 0.1
            dialogue = self._generate_karaoke_line(
                current_line_words,
                line_start,
                line_end,
            )
            lines.append(dialogue)

        # Write the file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Subtitles saved to {output_path}")
        return output_path

    def generate_simple_subtitles(
        self,
        transcription: "Transcription",
        output_path: Path,
        words_per_line: int = 4,
    ) -> Path:
        """Generate simple SRT-style subtitles without karaoke effect.

        This is a fallback for players that don't support ASS karaoke.

        Args:
            transcription: Transcription with word-level timestamps.
            output_path: Path to save the SRT file.
            words_per_line: Maximum words per subtitle line.

        Returns:
            Path to the generated subtitle file.
        """
        logger.info("Generating simple SRT subtitles")

        lines: list[str] = []
        subtitle_index = 1
        current_line_words: list[WordTimestamp] = []

        for word in transcription.words:
            current_line_words.append(word)

            should_end_line = len(
                current_line_words
            ) >= words_per_line or word.word.rstrip().endswith((".", "!", "?"))

            if should_end_line and current_line_words:
                start = current_line_words[0].start
                end = current_line_words[-1].end

                # Format times for SRT (HH:MM:SS,mmm)
                start_str = self._format_srt_time(start)
                end_str = self._format_srt_time(end)

                text = " ".join(w.word.strip() for w in current_line_words)

                lines.append(f"{subtitle_index}")
                lines.append(f"{start_str} --> {end_str}")
                lines.append(text)
                lines.append("")

                subtitle_index += 1
                current_line_words = []

        # Handle remaining words
        if current_line_words:
            start = current_line_words[0].start
            end = current_line_words[-1].end
            start_str = self._format_srt_time(start)
            end_str = self._format_srt_time(end)
            text = " ".join(w.word.strip() for w in current_line_words)

            lines.append(f"{subtitle_index}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(text)
            lines.append("")

        # Write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Simple subtitles saved to {output_path}")
        return output_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds.

        Returns:
            SRT formatted time string.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
