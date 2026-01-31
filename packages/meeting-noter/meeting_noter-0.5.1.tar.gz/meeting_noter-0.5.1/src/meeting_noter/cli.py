"""CLI commands for Meeting Noter."""

from __future__ import annotations

import click
from pathlib import Path
from typing import Optional

from meeting_noter import __version__
from meeting_noter.config import (
    get_config,
    require_setup,
    is_setup_complete,
    generate_meeting_name,
)


# Default paths
DEFAULT_PID_FILE = Path.home() / ".meeting-noter.pid"


def _launch_gui_background():
    """Launch the GUI in background and return immediately."""
    import subprocess
    import sys

    subprocess.Popen(
        [sys.executable, "-m", "meeting_noter.gui"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    click.echo("Meeting Noter GUI launched.")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """Meeting Noter - Offline meeting transcription.

    Run 'meeting-noter' to launch the GUI, or use subcommands:
    - setup: One-time setup (Screen Recording permission)
    - start <name>: Interactive foreground recording
    - gui: Launch desktop GUI
    - menubar: Launch menu bar app
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - launch GUI in background
        _launch_gui_background()


@cli.command()
def setup():
    """Set up Meeting Noter and initialize configuration.

    This is a one-time setup that:
    1. Requests Screen Recording permission (for capturing meeting audio)
    2. Initializes configuration file
    3. Creates recording directories
    """
    from meeting_noter.install.macos import run_setup

    config = get_config()

    # Run the setup
    run_setup()

    # Mark setup as complete and ensure directories exist
    config.setup_complete = True
    config.recordings_dir.mkdir(parents=True, exist_ok=True)
    config.transcripts_dir.mkdir(parents=True, exist_ok=True)
    config.save()

    click.echo(f"Recordings will be saved to: {config.recordings_dir}")
    click.echo(f"Whisper model: {config.whisper_model}")


@cli.command()
@click.argument("name", required=False)
@require_setup
def start(name: Optional[str]):
    """Start an interactive foreground recording session.

    NAME is the meeting name (optional). If not provided, uses a timestamp
    like "29_Jan_2026_1430".

    Examples:
        meeting-noter start                    # Uses timestamp name
        meeting-noter start "Weekly Standup"   # Uses custom name

    Press Ctrl+C to stop recording. The recording will be automatically
    transcribed if auto_transcribe is enabled in settings.
    """
    from meeting_noter.daemon import run_foreground_capture

    config = get_config()
    output_dir = config.recordings_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use default timestamp name if not provided
    meeting_name = name if name else generate_meeting_name()

    run_foreground_capture(
        output_dir=output_dir,
        meeting_name=meeting_name,
        auto_transcribe=config.auto_transcribe,
        whisper_model=config.whisper_model,
        transcripts_dir=config.transcripts_dir,
        silence_timeout_minutes=config.silence_timeout,
    )


@cli.command()
@click.option(
    "--output-dir", "-o",
    type=click.Path(),
    default=None,
    help="Directory to save recordings (overrides config)",
)
@click.option(
    "--foreground", "-f",
    is_flag=True,
    help="Run in foreground instead of as daemon",
)
@click.option(
    "--name", "-n",
    default=None,
    help="Meeting name for the recording",
)
@require_setup
def daemon(output_dir: Optional[str], foreground: bool, name: Optional[str]):
    """Start the background daemon to capture meeting audio.

    The daemon captures your microphone and system audio (via ScreenCaptureKit)
    and records to MP3 files. Files are automatically segmented when
    silence is detected (indicating a meeting has ended).
    """
    from meeting_noter.daemon import run_daemon

    config = get_config()
    output_path = Path(output_dir) if output_dir else config.recordings_dir
    output_path.mkdir(parents=True, exist_ok=True)

    run_daemon(
        output_path,
        foreground=foreground,
        pid_file=DEFAULT_PID_FILE,
        meeting_name=name,
    )


@cli.command()
@require_setup
def status():
    """Check if the daemon is running."""
    from meeting_noter.daemon import check_status
    check_status(DEFAULT_PID_FILE)


@cli.command()
@require_setup
def stop():
    """Stop the running daemon."""
    from meeting_noter.daemon import stop_daemon
    stop_daemon(DEFAULT_PID_FILE)


@cli.command("list")
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing recordings (overrides config)",
)
@click.option(
    "--limit", "-n",
    type=int,
    default=10,
    help="Number of recordings to show",
)
@require_setup
def list_recordings(output_dir: Optional[str], limit: int):
    """List recent meeting recordings."""
    from meeting_noter.output.writer import list_recordings as _list_recordings

    config = get_config()
    path = Path(output_dir) if output_dir else config.recordings_dir
    _list_recordings(path, limit)


@cli.command()
@click.argument("file", required=False)
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing recordings (overrides config)",
)
@click.option(
    "--model", "-m",
    type=click.Choice(["tiny.en", "base.en", "small.en", "medium.en", "large-v3"]),
    default=None,
    help="Whisper model size (overrides config)",
)
@click.option(
    "--live", "-l",
    is_flag=True,
    help="Real-time transcription of current recording",
)
@require_setup
def transcribe(file: Optional[str], output_dir: Optional[str], model: Optional[str], live: bool):
    """Transcribe a meeting recording.

    If no FILE is specified, transcribes the most recent recording.
    Use --live for real-time transcription of an ongoing meeting.
    """
    from meeting_noter.transcription.engine import transcribe_file, transcribe_live

    config = get_config()
    output_path = Path(output_dir) if output_dir else config.recordings_dir
    whisper_model = model or config.whisper_model

    if live:
        transcribe_live(output_path, whisper_model)
    else:
        transcribe_file(file, output_path, whisper_model, config.transcripts_dir)


@cli.command()
@click.option(
    "--foreground", "-f",
    is_flag=True,
    help="Run in foreground instead of background",
)
@require_setup
def menubar(foreground: bool):
    """Launch menu bar app for daemon control.

    Adds a menu bar icon for one-click start/stop of the recording daemon.
    The icon shows "MN" when idle and "MN [filename]" when recording.

    By default, runs in background. Use -f for foreground (debugging).
    """
    import subprocess
    import sys

    if foreground:
        from meeting_noter.menubar import run_menubar
        run_menubar()
    else:
        # Spawn as background process
        subprocess.Popen(
            [sys.executable, "-m", "meeting_noter.menubar"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        click.echo("Menu bar app started in background.")


@cli.command()
@click.option(
    "--foreground", "-f",
    is_flag=True,
    help="Run in foreground instead of background",
)
@require_setup
def gui(foreground: bool):
    """Launch the desktop GUI application.

    Opens a window with tabs for:
    - Recording: Start/stop recordings with meeting names
    - Meetings: Browse, play, and manage recordings
    - Settings: Configure directories, models, and preferences

    By default runs in background. Use -f for foreground.
    """
    if foreground:
        from meeting_noter.gui import run_gui
        run_gui()
    else:
        _launch_gui_background()


@cli.command()
def devices():
    """List available audio devices."""
    import sounddevice as sd

    devices = sd.query_devices()
    click.echo("\nAvailable Audio Devices:\n")

    for i, device in enumerate(devices):
        device_type = []
        if device["max_input_channels"] > 0:
            device_type.append("IN")
        if device["max_output_channels"] > 0:
            device_type.append("OUT")

        type_str = "/".join(device_type) if device_type else "N/A"
        click.echo(f"  [{i}] {device['name']} ({type_str})")

    click.echo()


if __name__ == "__main__":
    cli()
