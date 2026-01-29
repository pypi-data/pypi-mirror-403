"""Video processing utilities using MoviePy 2.x."""

import contextlib
import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

# MoviePy 2.x imports
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image

if TYPE_CHECKING:
    from video_composer.config import Settings
    from video_composer.models import StockFootage, Transcription, VideoSegment

logger = logging.getLogger(__name__)


class VideoProcessorError(Exception):
    """Base exception for video processing errors."""
    pass


class VideoProcessor:
    """Processor for video assembly and manipulation using MoviePy 2.x."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the video processor.

        Args:
            settings: Application settings for video configuration.
        """
        self.settings = settings
        self.width = settings.video_width
        self.height = settings.video_height
        self.fps = settings.video_fps

    @staticmethod
    def extract_frame(
        video_path: Path,
        output_path: Path,
        time_seconds: float,
    ) -> Path:
        """Extract a single frame from a video at a specific time.

        Args:
            video_path: Path to the video file.
            output_path: Path to save the extracted frame.
            time_seconds: Time position in seconds.

        Returns:
            Path to the extracted frame image.

        Raises:
            VideoProcessorError: If frame extraction fails.
        """
        logger.debug(f"Extracting frame at {time_seconds:.2f}s from {video_path}")

        try:
            clip = VideoFileClip(str(video_path))

            # Ensure time is within bounds
            time_seconds = min(max(0, time_seconds), clip.duration - 0.1)

            # Get the frame as a numpy array
            frame = clip.get_frame(time_seconds)

            # Save using PIL
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img = Image.fromarray(frame)
            img.save(str(output_path), quality=85)

            clip.close()

            logger.debug(f"Frame saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to extract frame: {e}")
            raise VideoProcessorError(f"Failed to extract frame: {e}") from e

    def prepare_clip(
        self,
        video_path: Path,
        target_duration: float,
        start_time: float = 0,
    ) -> VideoFileClip:
        """Prepare a video clip for composition.

        This method:
        1. Loads the video
        2. Crops/resizes to target aspect ratio (9:16)
        3. Trims to target duration
        4. Removes audio

        Args:
            video_path: Path to the source video.
            target_duration: Desired duration in seconds.
            start_time: Start time for trimming.

        Returns:
            Prepared VideoFileClip.
        """
        logger.debug(f"Preparing clip: {video_path} (duration: {target_duration}s)")

        clip = VideoFileClip(str(video_path))

        # Calculate crop dimensions for 9:16 aspect ratio
        target_ratio = self.width / self.height  # 9/16 = 0.5625
        current_ratio = clip.w / clip.h

        if current_ratio > target_ratio:
            # Video is wider than target - crop width
            new_width = int(clip.h * target_ratio)
            x_center = clip.w // 2
            x1 = x_center - new_width // 2
            clip = clip.cropped(x1=x1, x2=x1 + new_width)
        elif current_ratio < target_ratio:
            # Video is taller than target - crop height
            new_height = int(clip.w / target_ratio)
            y_center = clip.h // 2
            y1 = y_center - new_height // 2
            clip = clip.cropped(y1=y1, y2=y1 + new_height)

        # Resize to target dimensions
        clip = clip.resized((self.width, self.height))

        # Handle duration
        available_duration = clip.duration - start_time
        if available_duration < target_duration:
            # Loop the clip if it's too short
            loops_needed = int(target_duration / clip.duration) + 1
            clip = concatenate_videoclips([clip] * loops_needed)

        # Trim to target duration - MoviePy 2.x uses subclipped
        clip = clip.subclipped(start_time, start_time + target_duration)

        # Remove audio (we'll add our own)
        clip = clip.without_audio()

        return clip

    def create_segments_from_footage(
        self,
        footage_list: list["StockFootage"],
        transcription: "Transcription",
    ) -> list["VideoSegment"]:
        """Create video segments by distributing transcription across footage.

        Args:
            footage_list: List of validated stock footage.
            transcription: Transcription with word timestamps.

        Returns:
            List of VideoSegment objects.
        """
        from video_composer.models import VideoSegment

        if not footage_list:
            raise VideoProcessorError("No footage provided")

        if not transcription.words:
            raise VideoProcessorError("No words in transcription")

        segments: list[VideoSegment] = []
        total_duration = transcription.duration

        # Distribute duration evenly across footage clips
        segment_duration = total_duration / len(footage_list)

        current_time = 0.0
        word_index = 0

        for footage in footage_list:
            segment_start = current_time
            segment_end = min(current_time + segment_duration, total_duration)

            # Collect words for this segment
            segment_words = []
            while word_index < len(transcription.words):
                word = transcription.words[word_index]
                # Include word if it starts within this segment
                if word.start < segment_end:
                    segment_words.append(word)
                    word_index += 1
                else:
                    break

            segments.append(
                VideoSegment(
                    footage=footage,
                    start_time=segment_start,
                    end_time=segment_end,
                    words=segment_words,
                )
            )

            current_time = segment_end

        # Adjust last segment to include any remaining words
        if word_index < len(transcription.words) and segments:
            segments[-1].words.extend(transcription.words[word_index:])
            segments[-1] = VideoSegment(
                footage=segments[-1].footage,
                start_time=segments[-1].start_time,
                end_time=transcription.words[-1].end,
                words=segments[-1].words,
            )

        logger.info(f"Created {len(segments)} video segments")
        return segments

    def compose_video(
        self,
        segments: list["VideoSegment"],
        audio_path: Path,
        subtitle_path: Path | None,
        output_path: Path,
    ) -> Path:
        """Compose the final video from segments, audio, and subtitles.

        Args:
            segments: List of video segments.
            audio_path: Path to the audio file.
            subtitle_path: Optional path to ASS subtitle file.
            output_path: Path for the output video.

        Returns:
            Path to the composed video.

        Raises:
            VideoProcessorError: If composition fails.
        """
        logger.info(f"Composing video with {len(segments)} segments")

        clips: list[VideoFileClip] = []

        try:
            # Prepare each segment
            for i, segment in enumerate(segments):
                logger.debug(f"Processing segment {i + 1}/{len(segments)}")
                clip = self.prepare_clip(
                    segment.footage.local_path,
                    segment.duration,
                )
                clips.append(clip)

            # Concatenate all clips
            if len(clips) == 1:
                final_video = clips[0]
            else:
                final_video = concatenate_videoclips(clips, method="compose")

            # Load and attach audio - MoviePy 2.x uses with_audio
            audio = AudioFileClip(str(audio_path))
            final_video = final_video.with_audio(audio)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # If we have subtitles, we need to burn them in using ffmpeg
            if subtitle_path and subtitle_path.exists():
                # First, export video without subtitles to a temp file
                temp_video = output_path.parent / f"temp_{output_path.name}"

                logger.info("Exporting video (without subtitles)...")
                final_video.write_videofile(
                    str(temp_video),
                    fps=self.fps,
                    codec=self.settings.video_codec,
                    audio_codec=self.settings.audio_codec,
                    preset="medium",
                    threads=4,
                    logger=None,  # Suppress moviepy's verbose output
                )

                # Close clips before ffmpeg processing
                final_video.close()
                audio.close()
                for clip in clips:
                    clip.close()

                # Burn in subtitles using ffmpeg
                logger.info("Burning in subtitles...")
                self._burn_subtitles(temp_video, subtitle_path, output_path)

                # Clean up temp file
                if temp_video.exists():
                    temp_video.unlink()
            else:
                # Export directly without subtitles
                logger.info("Exporting final video...")
                final_video.write_videofile(
                    str(output_path),
                    fps=self.fps,
                    codec=self.settings.video_codec,
                    audio_codec=self.settings.audio_codec,
                    preset="medium",
                    threads=4,
                    logger=None,
                )

                # Close all clips
                final_video.close()
                audio.close()
                for clip in clips:
                    clip.close()

            logger.info(f"Video composed successfully: {output_path}")
            return output_path

        except Exception as e:
            # Clean up on error
            for clip in clips:
                with contextlib.suppress(Exception):
                    clip.close()
            logger.error(f"Failed to compose video: {e}")
            raise VideoProcessorError(f"Failed to compose video: {e}") from e

    def _burn_subtitles(
        self,
        video_path: Path,
        subtitle_path: Path,
        output_path: Path,
    ) -> None:
        """Burn subtitles into video using ffmpeg.

        Args:
            video_path: Path to the input video.
            subtitle_path: Path to the ASS subtitle file.
            output_path: Path for the output video.

        Raises:
            VideoProcessorError: If subtitle burning fails.
        """
        # Escape paths for ffmpeg filter
        subtitle_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"ass={subtitle_path_escaped}",
            "-c:a",
            "copy",
            "-y",  # Overwrite output
            str(output_path),
        ]

        logger.debug(f"Running ffmpeg: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug(f"ffmpeg output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr}")
            raise VideoProcessorError(f"Failed to burn subtitles: {e.stderr}") from e
        except FileNotFoundError as e:
            raise VideoProcessorError(
                "ffmpeg not found. Please install ffmpeg and ensure it's in your PATH."
            ) from e

    def create_background_clip(
        self,
        duration: float,
        color: tuple[int, int, int] = (0, 0, 0),
    ) -> ColorClip:
        """Create a solid color background clip.

        Args:
            duration: Duration in seconds.
            color: RGB color tuple.

        Returns:
            ColorClip with specified properties.
        """
        return ColorClip(
            size=(self.width, self.height),
            color=color,
            duration=duration,
        )

    def add_overlay(
        self,
        base_clip: VideoFileClip,
        overlay_clip: VideoFileClip,
        position: tuple[int | str, int | str] = ("center", "center"),
        opacity: float = 1.0,
    ) -> CompositeVideoClip:
        """Add an overlay clip on top of a base clip.

        Args:
            base_clip: The background video clip.
            overlay_clip: The clip to overlay.
            position: Position tuple (x, y) or named positions.
            opacity: Overlay opacity (0-1).

        Returns:
            CompositeVideoClip with overlay applied.
        """
        if opacity < 1.0:
            overlay_clip = overlay_clip.with_opacity(opacity)

        return CompositeVideoClip(
            [base_clip, overlay_clip.with_position(position)],
            size=(self.width, self.height),
        )

    def get_video_info(self, video_path: Path) -> dict:
        """Get information about a video file.

        Args:
            video_path: Path to the video file.

        Returns:
            Dictionary with video properties.
        """
        clip = VideoFileClip(str(video_path))
        info = {
            "duration": clip.duration,
            "fps": clip.fps,
            "width": clip.w,
            "height": clip.h,
            "aspect_ratio": clip.w / clip.h if clip.h > 0 else 0,
        }
        clip.close()
        return info
