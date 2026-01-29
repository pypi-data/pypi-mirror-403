"""CLI interface for the video composer using Typer."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Annotated, Literal, cast

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from video_composer.composer import VideoComposer
from video_composer.config import Settings
from video_composer.utils.subtitles import normalize_ass_color

# Initialize Typer app
app = typer.Typer(
    name="video-composer",
    help="Social video automation tool for generating vertical short-form marketing videos.",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich handler.

    Args:
        verbose: Whether to enable verbose (DEBUG) logging.
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("moviepy").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def validate_api_keys() -> tuple[bool, list[str]]:
    """Validate that required API keys are configured.

    Returns:
        Tuple of (is_valid, list of missing keys).
    """
    missing = []

    try:
        settings = Settings()  # type: ignore[call-arg]
    except Exception:
        # If settings can't load, keys are probably missing
        return False, ["OPENAI_API_KEY", "PEXELS_API_KEY or PIXABAY_API_KEY"]

    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")

    # Check the appropriate stock provider API key
    if settings.stock_provider == "pixabay":
        if not settings.pixabay_api_key:
            missing.append("PIXABAY_API_KEY")
    else:
        if not settings.pexels_api_key:
            missing.append("PEXELS_API_KEY")

    return len(missing) == 0, missing


@app.command()
def create(
    script: Annotated[
        str,
        typer.Option(
            "--script",
            "-s",
            help="The marketing script text to convert to video.",
        ),
    ],
    keywords: Annotated[
        list[str],
        typer.Option(
            "--keyword",
            "-k",
            help="Keywords for stock footage (can specify multiple).",
        ),
    ],
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Output filename (without extension).",
        ),
    ] = None,
    context: Annotated[
        str | None,
        typer.Option(
            "--context",
            "-c",
            help="Additional context for video validation.",
        ),
    ] = None,
    subtitle_font: Annotated[
        str | None,
        typer.Option(
            "--subtitle-font",
            help="Subtitle font family.",
        ),
    ] = None,
    subtitle_font_size: Annotated[
        int | None,
        typer.Option(
            "--subtitle-font-size",
            help="Subtitle font size.",
        ),
    ] = None,
    subtitle_primary_color: Annotated[
        str | None,
        typer.Option(
            "--subtitle-primary-color",
            help="Subtitle primary color (#RRGGBB or ASS).",
        ),
    ] = None,
    subtitle_highlight_color: Annotated[
        str | None,
        typer.Option(
            "--subtitle-highlight-color",
            help="Subtitle highlight color (#RRGGBB or ASS).",
        ),
    ] = None,
    subtitle_outline_color: Annotated[
        str | None,
        typer.Option(
            "--subtitle-outline-color",
            help="Subtitle outline color (#RRGGBB or ASS).",
        ),
    ] = None,
    subtitle_outline_width: Annotated[
        int | None,
        typer.Option(
            "--subtitle-outline-width",
            help="Subtitle outline width.",
        ),
    ] = None,
    subtitle_shadow_depth: Annotated[
        int | None,
        typer.Option(
            "--subtitle-shadow-depth",
            help="Subtitle shadow depth.",
        ),
    ] = None,
    subtitle_position: Annotated[
        str | None,
        typer.Option(
            "--subtitle-position",
            help="Subtitle position: top, center, or bottom.",
        ),
    ] = None,
    subtitle_margin: Annotated[
        int | None,
        typer.Option(
            "--subtitle-margin",
            help="Subtitle bottom margin in pixels.",
        ),
    ] = None,
    subtitle_words_per_line: Annotated[
        int | None,
        typer.Option(
            "--subtitle-words-per-line",
            help="Maximum words per subtitle line.",
        ),
    ] = None,
    subtitles_enabled: Annotated[
        bool | None,
        typer.Option(
            "--subtitles-enabled/--no-subtitles",
            help="Enable or disable subtitles.",
        ),
    ] = None,
    keep_temp: Annotated[
        bool,
        typer.Option(
            "--keep-temp",
            help="Keep temporary files after processing.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging.",
        ),
    ] = False,
) -> None:
    """Create a marketing video from script and keywords.

    Example:
        video-composer create -s "Welcome to the future of technology" -k technology -k innovation -k success
    """
    setup_logging(verbose)

    # Validate API keys
    keys_valid, missing_keys = validate_api_keys()
    if not keys_valid:
        console.print(
            Panel(
                "[red]Missing required API keys:[/red]\n"
                + "\n".join(f"  - {key}" for key in missing_keys)
                + "\n\n[yellow]Please set these in your .env file or environment variables.[/yellow]",
                title="Configuration Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[bold]Script:[/bold] {script[:100]}{'...' if len(script) > 100 else ''}\n"
            f"[bold]Keywords:[/bold] {', '.join(keywords)}\n"
            f"[bold]Output:[/bold] {output or 'auto-generated'}",
            title="Video Composition",
            border_style="blue",
        )
    )

    async def run_composition() -> None:
        async with VideoComposer() as composer:
            if subtitle_font is not None:
                composer.settings.subtitle_font = subtitle_font
            if subtitle_font_size is not None:
                composer.settings.subtitle_font_size = subtitle_font_size
            if subtitle_primary_color is not None:
                composer.settings.subtitle_primary_color = normalize_ass_color(
                    subtitle_primary_color
                )
            if subtitle_highlight_color is not None:
                composer.settings.subtitle_highlight_color = normalize_ass_color(
                    subtitle_highlight_color
                )
            if subtitle_outline_color is not None:
                composer.settings.subtitle_outline_color = normalize_ass_color(
                    subtitle_outline_color
                )
            if subtitle_outline_width is not None:
                composer.settings.subtitle_outline_width = subtitle_outline_width
            if subtitle_shadow_depth is not None:
                composer.settings.subtitle_shadow_depth = subtitle_shadow_depth
            if subtitle_position is not None:
                normalized_position = subtitle_position.lower()
                if normalized_position not in ("top", "center", "bottom"):
                    raise typer.BadParameter("Subtitle position must be top, center, or bottom.")
                composer.settings.subtitle_position = cast(
                    Literal["top", "center", "bottom"],
                    normalized_position,
                )
            if subtitle_margin is not None:
                composer.settings.subtitle_margin_bottom = subtitle_margin
            if subtitle_words_per_line is not None:
                composer.settings.subtitle_words_per_line = subtitle_words_per_line
            if subtitles_enabled is not None:
                composer.settings.subtitles_enabled = subtitles_enabled

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating video...", total=None)

                result = await composer.create_video(
                    script=script,
                    keywords=keywords,
                    output_filename=output,
                    validation_context=context,
                    cleanup_temp=not keep_temp,
                    words_per_line=subtitle_words_per_line,
                    subtitles_enabled=subtitles_enabled,
                )

                progress.update(task, completed=True)

            if result.success:
                console.print(
                    Panel(
                        f"[green]Video created successfully![/green]\n\n"
                        f"[bold]Output:[/bold] {result.output_path}\n"
                        f"[bold]Duration:[/bold] {result.duration:.2f}s",
                        title="Success",
                        border_style="green",
                    )
                )

                if result.warnings:
                    for warning in result.warnings:
                        console.print(f"[yellow]Warning:[/yellow] {warning}")
            else:
                console.print(
                    Panel(
                        f"[red]Video creation failed[/red]\n\n[bold]Error:[/bold] {result.error}",
                        title="Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

    asyncio.run(run_composition())


@app.command()
def tts(
    script: Annotated[
        str,
        typer.Option(
            "--script",
            "-s",
            help="Text to convert to speech.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output audio file path.",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging.",
        ),
    ] = False,
) -> None:
    """Generate text-to-speech audio only.

    Example:
        video-composer tts -s "Hello world" -o output.mp3
    """
    setup_logging(verbose)

    async def run_tts() -> None:
        async with VideoComposer() as composer:
            result = await composer.generate_tts_only(script, output)
            console.print(f"[green]Audio saved to:[/green] {result}")

    asyncio.run(run_tts())


@app.command()
def transcribe(
    audio: Annotated[
        Path,
        typer.Option(
            "--audio",
            "-a",
            help="Audio file to transcribe.",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output JSON file for transcription.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging.",
        ),
    ] = False,
) -> None:
    """Transcribe audio with word-level timestamps.

    Example:
        video-composer transcribe -a input.mp3 -o transcription.json
    """
    setup_logging(verbose)

    if not audio.exists():
        console.print(f"[red]Audio file not found:[/red] {audio}")
        raise typer.Exit(1)

    async def run_transcribe() -> None:
        async with VideoComposer() as composer:
            transcription = await composer.transcribe_audio_only(audio)

            # Display results
            table = Table(title="Transcription Results")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row(
                "Text",
                transcription.text[:100] + "..."
                if len(transcription.text) > 100
                else transcription.text,
            )
            table.add_row("Words", str(len(transcription.words)))
            table.add_row("Duration", f"{transcription.duration:.2f}s")

            console.print(table)

            # Save to JSON if output specified
            if output:
                import json

                data = {
                    "text": transcription.text,
                    "duration": transcription.duration,
                    "words": [
                        {
                            "word": w.word,
                            "start": w.start,
                            "end": w.end,
                        }
                        for w in transcription.words
                    ],
                }

                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w") as f:
                    json.dump(data, f, indent=2)

                console.print(f"[green]Transcription saved to:[/green] {output}")

    asyncio.run(run_transcribe())


@app.command()
def search_footage(
    keywords: Annotated[
        list[str],
        typer.Option(
            "--keyword",
            "-k",
            help="Keywords to search for (can specify multiple).",
        ),
    ],
    validate: Annotated[
        bool,
        typer.Option(
            "--validate/--no-validate",
            help="Validate footage with Vision API.",
        ),
    ] = True,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Directory to save downloaded footage.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging.",
        ),
    ] = False,
) -> None:
    """Search and download stock footage using configured provider.

    Example:
        video-composer search-footage -k nature -k sunset --output-dir ./footage
    """
    setup_logging(verbose)

    async def run_search() -> None:
        # Import here to avoid circular imports at module level
        from video_composer.services.openai_service import OpenAIService
        from video_composer.services.pexels_service import PexelsService
        from video_composer.services.pixabay_service import PixabayService

        settings = Settings()  # type: ignore[call-arg]

        # Get the configured provider
        openai_svc = OpenAIService(settings) if validate else None

        if settings.stock_provider == "pixabay":
            provider = PixabayService(settings, openai_svc)
            provider_name = "Pixabay"
        else:
            provider = PexelsService(settings, openai_svc)
            provider_name = "Pexels"

        console.print(f"[dim]Using {provider_name} as stock provider[/dim]")

        async with provider:
            if validate and openai_svc:
                async with openai_svc:
                    footage = await provider.get_multiple_footage(
                        keywords,
                        output_dir or Path("./footage"),
                    )
            else:
                footage = await provider.get_multiple_footage(
                    keywords,
                    output_dir or Path("./footage"),
                )

            # Display results
            table = Table(title="Downloaded Footage")
            table.add_column("Keyword", style="cyan")
            table.add_column("Video ID", style="green")
            table.add_column("Path", style="yellow")
            table.add_column("Validated", style="magenta")

            for kw, f in footage.items():
                table.add_row(
                    kw,
                    str(f.video.id),
                    str(f.local_path),
                    "Yes" if f.is_validated else "No",
                )

            console.print(table)

    asyncio.run(run_search())


@app.command()
def from_yaml(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to YAML configuration file.",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging.",
        ),
    ] = False,
) -> None:
    """Generate videos from a YAML configuration file.

    Supports both single video and batch configurations.

    Example:
        video-composer from-yaml videos.yaml
        video-composer from-yaml batch_config.yaml -v
    """
    setup_logging(verbose)

    # Validate API keys
    keys_valid, missing_keys = validate_api_keys()
    if not keys_valid:
        console.print(
            Panel(
                "[red]Missing required API keys:[/red]\n"
                + "\n".join(f"  - {key}" for key in missing_keys)
                + "\n\n[yellow]Please set these in your .env file or environment variables.[/yellow]",
                title="Configuration Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    if not config_file.exists():
        console.print(f"[red]Config file not found:[/red] {config_file}")
        raise typer.Exit(1)

    async def run_yaml() -> None:
        from video_composer.batch_processor import process_yaml

        results = await process_yaml(config_file, verbose)

        # Check for failures
        failed = sum(1 for r in results if r["status"] != "success")
        if failed > 0:
            raise typer.Exit(1)

    asyncio.run(run_yaml())


@app.command()
def init_config(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output path for the YAML template.",
        ),
    ] = Path("videos.yaml"),
    batch: Annotated[
        bool,
        typer.Option(
            "--batch",
            "-b",
            help="Create a batch configuration template.",
        ),
    ] = False,
) -> None:
    """Create a sample YAML configuration file.

    Example:
        video-composer init-config
        video-composer init-config -o my_videos.yaml --batch
    """
    if batch:
        template = """# Batch Video Configuration
# Generate multiple videos from a single config file

version: "1.0"

# Global defaults (can be overridden per video)
voice:
  model: tts-1-hd
  voice: nova
  speed: 1.0

subtitles:
  enabled: true
  font: Arial
  font_size: 48
  primary_color: "#FFFFFF"
  highlight_color: "#FFFF00"
  outline_color: "#000000"
  outline_width: 3
  shadow_depth: 2
  position: bottom
  margin: 150
  words_per_line: 4

video:
  width: 1080
  height: 1920
  fps: 30
  quality: high

# Output settings
output_dir: ./output
keep_temp: false

# Videos to generate
videos:
  - name: motivation_monday
    script: |
      Every successful person started exactly where you are right now.
      The difference? They didn't give up.
      Your dreams are valid. Your goals are achievable.
      Start today. Start now.
    keywords:
      - sunrise motivation
      - person working hard
      - success celebration
      - determination focus

  - name: tech_innovation
    script: |
      Welcome to the future of technology.
      Innovation drives success in today's fast-paced world.
      Join us on this incredible journey of discovery and transformation.
    keywords:
      - technology
      - innovation
      - futuristic
    # Override voice for this video
    voice:
      voice: onyx

  - name: product_launch
    script: |
      Introducing the next generation of productivity.
      Work smarter. Achieve more. Live better.
      Available now. Link in bio.
    keywords:
      - smartphone app
      - productivity
      - business success
    output_filename: product_promo
"""
    else:
        template = """# Single Video Configuration
# Simple format for generating one video

script: |
  Every successful person started exactly where you are right now.
  The difference? They didn't give up.
  Your dreams are valid. Your goals are achievable.
  Start today. Start now. Your future self will thank you.

keywords:
  - sunrise motivation
  - person working hard
  - success celebration
  - determination focus
  - mountain peak
  - runner athlete

# Voice settings
voice:
  model: tts-1-hd
  voice: nova
  speed: 1.0

# Subtitle settings
subtitles:
  enabled: true
  font: Arial
  font_size: 48
  primary_color: "#FFFFFF"
  highlight_color: "#FFFF00"
  outline_color: "#000000"
  outline_width: 3
  shadow_depth: 2
  position: bottom
  margin: 150
  words_per_line: 4

# Video settings
video:
  width: 1080
  height: 1920
  fps: 30
  quality: high

# Output settings
output_filename: my_video
output_dir: ./output
keep_temp: false
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template)
    console.print(f"[green]Created config template:[/green] {output}")
    console.print(f"\n[dim]Edit the file and run:[/dim] video-composer from-yaml {output}")


@app.command()
def version() -> None:
    """Show version information."""
    from video_composer import __version__

    console.print(f"video-composer version {__version__}")


@app.command()
def config() -> None:
    """Show current configuration."""
    try:
        settings = Settings()  # type: ignore[call-arg]
    except Exception as e:
        console.print(f"[red]Failed to load configuration:[/red] {e}")
        raise typer.Exit(1) from None

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Video settings
    table.add_row("Video Width", str(settings.video_width))
    table.add_row("Video Height", str(settings.video_height))
    table.add_row("Video FPS", str(settings.video_fps))

    # TTS settings
    table.add_row("TTS Model", settings.tts_model)
    table.add_row("TTS Voice", settings.tts_voice)

    # Paths
    table.add_row("Temp Directory", str(settings.temp_dir))
    table.add_row("Output Directory", str(settings.output_dir))

    # Stock provider
    table.add_row("Stock Provider", settings.stock_provider)

    # API Keys (masked)
    table.add_row(
        "OpenAI API Key",
        "***" + settings.openai_api_key[-4:] if settings.openai_api_key else "[red]Not set[/red]",
    )
    table.add_row(
        "Pexels API Key",
        "***" + settings.pexels_api_key[-4:] if settings.pexels_api_key else "[red]Not set[/red]",
    )
    table.add_row(
        "Pixabay API Key",
        "***" + settings.pixabay_api_key[-4:] if settings.pixabay_api_key else "[red]Not set[/red]",
    )

    console.print(table)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
