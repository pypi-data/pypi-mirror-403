"""Batch video processor for YAML-based configuration."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from video_composer.composer import VideoComposer
from video_composer.yaml_config.video_config import (
    BatchConfig,
    SingleVideoConfig,
    SubtitleConfig,
    VoiceConfig,
)

logger = logging.getLogger(__name__)
console = Console()


class BatchProcessorError(Exception):
    """Error during batch processing."""
    pass


class YAMLLoader:
    """Load and validate YAML configuration files."""

    @staticmethod
    def load_file(path: Path) -> dict[str, Any]:
        """Load YAML file and return parsed content."""
        if not path.exists():
            raise BatchProcessorError(f"Config file not found: {path}")

        if path.suffix.lower() not in (".yaml", ".yml"):
            raise BatchProcessorError(f"File must be .yaml or .yml: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if not content:
                raise BatchProcessorError(f"Empty config file: {path}")

            return content

        except yaml.YAMLError as e:
            raise BatchProcessorError(f"Invalid YAML syntax: {e}") from e

    @staticmethod
    def parse_batch_config(data: dict[str, Any]) -> BatchConfig:
        """Parse and validate batch configuration."""
        try:
            return BatchConfig(**data)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(part) for part in error["loc"])
                errors.append(f"  {loc}: {error['msg']}")
            raise BatchProcessorError(
                "Invalid batch configuration:\n" + "\n".join(errors)
            ) from e

    @staticmethod
    def parse_single_config(data: dict[str, Any]) -> SingleVideoConfig:
        """Parse and validate single video configuration."""
        try:
            return SingleVideoConfig(**data)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(part) for part in error["loc"])
                errors.append(f"  {loc}: {error['msg']}")
            raise BatchProcessorError(
                "Invalid configuration:\n" + "\n".join(errors)
            ) from e

    @classmethod
    def load(cls, path: Path) -> BatchConfig | SingleVideoConfig:
        """Load and parse YAML config, auto-detecting format."""
        data = cls.load_file(path)

        # Detect if it's a batch config (has 'videos' key) or single video
        if "videos" in data:
            return cls.parse_batch_config(data)
        else:
            return cls.parse_single_config(data)


class BatchProcessor:
    """Process batch video generation from YAML config."""

    def __init__(self, config_path: Path, verbose: bool = False):
        self.config_path = config_path
        self.verbose = verbose
        self.results: list[dict] = []

    async def process(self) -> list[dict]:
        """Process all videos in the configuration."""
        console.print(Panel(
            f"[bold blue]Loading configuration from:[/] {self.config_path}",
            title="Batch Video Processor"
        ))

        # Load config
        config = YAMLLoader.load(self.config_path)

        if isinstance(config, SingleVideoConfig):
            # Single video mode
            return await self._process_single(config)
        else:
            # Batch mode
            return await self._process_batch(config)

    async def _process_single(self, config: SingleVideoConfig) -> list[dict]:
        """Process a single video configuration."""
        console.print("\n[bold]Processing single video...[/]")

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = config.output_filename or f"video_{timestamp}"

        result = await self._create_video(
            script=config.script,
            keywords=config.keywords,
            output_path=output_dir / f"{output_name}.mp4",
            voice_config=config.voice,
            subtitle_config=config.subtitles,
            context=config.context,
            keep_temp=config.keep_temp,
        )

        self.results.append(result)
        self._print_results()
        return self.results

    async def _process_batch(self, config: BatchConfig) -> list[dict]:
        """Process batch video configuration."""
        total = len(config.videos)
        console.print(f"\n[bold]Processing {total} videos...[/]\n")

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Show video list
        table = Table(title="Videos to Generate")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Keywords", style="green")
        table.add_column("Script Preview", style="white")

        for i, video in enumerate(config.videos, 1):
            script_preview = video.script[:50] + "..." if len(video.script) > 50 else video.script
            table.add_row(
                str(i),
                video.name,
                ", ".join(video.keywords[:3]) + ("..." if len(video.keywords) > 3 else ""),
                script_preview
            )

        console.print(table)
        console.print()

        # Process each video
        for i, video in enumerate(config.videos, 1):
            console.print(f"\n[bold cyan]━━━ Video {i}/{total}: {video.name} ━━━[/]\n")

            # Merge configs (video-specific overrides global)
            voice_config = video.voice or config.voice
            subtitle_config = video.subtitles or config.subtitles

            output_name = video.output_filename or video.name
            output_path = output_dir / f"{output_name}.mp4"

            result = await self._create_video(
                script=video.script,
                keywords=video.keywords,
                output_path=output_path,
                voice_config=voice_config,
                subtitle_config=subtitle_config,
                context=video.context,
                keep_temp=config.keep_temp,
                video_name=video.name,
            )

            self.results.append(result)

        self._print_results()
        return self.results

    async def _create_video(
        self,
        script: str,
        keywords: list[str],
        output_path: Path,
        voice_config: VoiceConfig,
        subtitle_config: SubtitleConfig,
        context: str | None = None,
        keep_temp: bool = False,
        video_name: str | None = None,
    ) -> dict:
        """Create a single video."""
        start_time = datetime.now()
        result = {
            "name": video_name or output_path.stem,
            "output": str(output_path),
            "status": "pending",
            "duration": None,
            "size": None,
            "error": None,
        }

        try:
            async with VideoComposer() as composer:
                # Update composer settings based on config
                composer.settings.tts_voice = voice_config.voice
                composer.settings.tts_model = voice_config.model
                composer.settings.tts_speed = voice_config.speed

                composer.settings.subtitle_font = subtitle_config.font
                composer.settings.subtitle_font_size = subtitle_config.font_size
                composer.settings.subtitle_margin_bottom = subtitle_config.margin

                composition_result = await composer.create_video(
                    script=script,
                    keywords=keywords,
                    output_filename=output_path.stem,
                    validation_context=context,
                    cleanup_temp=not keep_temp,
                )

            # Get file info from CompositionResult
            if composition_result.success and composition_result.output_path:
                result["status"] = "success"
                result["output"] = str(composition_result.output_path)
                result["duration"] = composition_result.duration

                # Get file size
                if composition_result.output_path.exists():
                    result["size"] = composition_result.output_path.stat().st_size
            elif not composition_result.success:
                result["status"] = "failed"
                result["error"] = composition_result.error or "Unknown error"

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Failed to create video: {e}")
            console.print(f"[red]Error: {e}[/]")

        result["processing_time"] = (datetime.now() - start_time).total_seconds()
        return result

    def _print_results(self) -> None:
        """Print summary of results."""
        console.print("\n")

        table = Table(title="Generation Results")
        table.add_column("Video", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Duration", style="dim")
        table.add_column("Size", style="dim")
        table.add_column("Time", style="dim")

        success = 0
        failed = 0

        for r in self.results:
            status_style = "green" if r["status"] == "success" else "red"
            status_text = "✓ Success" if r["status"] == "success" else f"✗ Failed: {r.get('error', 'Unknown')[:30]}"

            duration = f"{r['duration']:.1f}s" if r.get("duration") else "-"
            size = f"{r['size'] / 1024 / 1024:.1f}MB" if r.get("size") else "-"
            proc_time = f"{r['processing_time']:.1f}s" if r.get("processing_time") else "-"

            table.add_row(
                r["name"],
                f"[{status_style}]{status_text}[/]",
                duration,
                size,
                proc_time,
            )

            if r["status"] == "success":
                success += 1
            else:
                failed += 1

        console.print(table)
        console.print(f"\n[bold]Summary:[/] {success} succeeded, {failed} failed\n")


async def process_yaml(config_path: Path, verbose: bool = False) -> list[dict]:
    """Main entry point for YAML processing."""
    processor = BatchProcessor(config_path, verbose)
    return await processor.process()
