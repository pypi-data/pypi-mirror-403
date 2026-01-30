"""
Command-line interface implementation for fmus-vox.

This module uses Typer to provide a rich CLI experience for interacting with
the fmus-vox library functionality.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, SpinnerColumn
from rich.live import Live
from rich.table import Table

from fmus_vox import Audio, transcribe, speak, VoiceStream, clone_voice
from fmus_vox.api import serve as api_serve
from fmus_vox.core.errors import FmusVoxError, DependencyError
from fmus_vox.stream.microphone import Microphone
from fmus_vox.stream.audioplayer import AudioPlayer
from fmus_vox.cli.helpers import get_output_path, interactive_mode, format_transcript

# Create the Typer app
app = typer.Typer(
    name="fmus-vox",
    help="Human-oriented speech processing toolkit",
    add_completion=False,
)

# Create console for rich output
console = Console()

@app.command("transcribe")
def transcribe_cmd(
    input_path: Path = typer.Argument(
        ...,
        help="Path to input audio file",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for transcription (default: stdout)",
    ),
    model: str = typer.Option(
        "whisper",
        "--model",
        "-m",
        help="STT model to use",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Language code (e.g., 'en', 'fr')",
    ),
    timestamps: bool = typer.Option(
        False,
        "--timestamps",
        "-t",
        help="Include timestamps in output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
):
    """Transcribe audio file to text."""
    try:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Transcribing audio...", total=None)

            # Load audio file
            audio = Audio.load(input_path)

            # Transcribe audio
            result = transcribe(
                audio,
                model=model,
                language=language,
                timestamps=timestamps,
            )

            progress.update(task, completed=100)

        # Format the output
        output_text = format_transcript(result, timestamps=timestamps)

        # Handle output
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(output_text)
            console.print(f"[green]Transcript saved to:[/green] {output}")
        else:
            console.print(output_text)

    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("speak")
def speak_cmd(
    text: str = typer.Argument(
        ...,
        help="Text to synthesize",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output audio file",
    ),
    voice: str = typer.Option(
        "default",
        "--voice",
        "-v",
        help="Voice to use",
    ),
    model: str = typer.Option(
        "vits",
        "--model",
        "-m",
        help="TTS model to use",
    ),
    speed: float = typer.Option(
        1.0,
        "--speed",
        "-s",
        help="Speaking speed (0.5-2.0)",
        min=0.5,
        max=2.0,
    ),
    play: bool = typer.Option(
        False,
        "--play",
        "-p",
        help="Play audio after synthesis",
    ),
):
    """Synthesize text to speech."""
    try:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Synthesizing speech...", total=None)

            # Generate speech
            audio = speak(
                text,
                voice=voice,
                model=model,
                speed=speed,
            )

            progress.update(task, completed=100)

        # Save audio
        output_path = get_output_path(output)
        audio.save(output_path)
        console.print(f"[green]Audio saved to:[/green] {output_path}")

        # Play if requested
        if play:
            console.print("[blue]Playing audio...[/blue]")
            audio.play()

    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("interact")
def interact_cmd(
    wake_word: str = typer.Option(
        "hey vox",
        "--wake-word",
        "-w",
        help="Wake word to trigger interaction",
    ),
    stt_model: str = typer.Option(
        "whisper",
        "--stt-model",
        "-s",
        help="Speech-to-text model",
    ),
    tts_model: str = typer.Option(
        "vits",
        "--tts-model",
        "-t",
        help="Text-to-speech model",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Language code (e.g., 'en', 'fr')",
    ),
    voice: str = typer.Option(
        "default",
        "--voice",
        "-v",
        help="TTS voice to use",
    ),
):
    """Start interactive voice mode."""
    try:
        console.print(f"[bold blue]Starting interactive mode with wake word:[/bold blue] '{wake_word}'")
        console.print("[blue]Press Ctrl+C to exit[/blue]")

        # Start interactive mode
        interactive_mode(
            wake_word=wake_word,
            stt_model=stt_model,
            tts_model=tts_model,
            language=language,
            voice=voice,
            console=console,
        )

    except KeyboardInterrupt:
        console.print("\n[blue]Exiting interactive mode[/blue]")
    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("clone")
def clone_cmd(
    reference_audio: Path = typer.Argument(
        ...,
        help="Reference audio for voice cloning",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    text: str = typer.Argument(
        ...,
        help="Text to synthesize with cloned voice",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output audio file",
    ),
    model: str = typer.Option(
        "yourtts",
        "--model",
        "-m",
        help="Voice cloning model to use",
    ),
    play: bool = typer.Option(
        False,
        "--play",
        "-p",
        help="Play audio after synthesis",
    ),
):
    """Clone voice and synthesize text."""
    try:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            load_task = progress.add_task("Loading reference audio...", total=100)
            progress.update(load_task, completed=30)

            # Load reference audio
            reference = Audio.load(reference_audio)
            progress.update(load_task, completed=100)

            clone_task = progress.add_task("Cloning voice...", total=100)

            # Clone voice and synthesize
            audio = clone_voice(reference, text, model=model)
            progress.update(clone_task, completed=100)

        # Save audio
        output_path = get_output_path(output)
        audio.save(output_path)
        console.print(f"[green]Cloned voice audio saved to:[/green] {output_path}")

        # Play if requested
        if play:
            console.print("[blue]Playing audio...[/blue]")
            audio.play()

    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("record")
def record_cmd(
    output: Path = typer.Argument(
        ...,
        help="Output audio file",
    ),
    device: Optional[int] = typer.Option(
        None,
        "--device",
        "-d",
        help="Input device index (use 'devices' command to list)",
    ),
    duration: Optional[float] = typer.Option(
        None,
        "--duration",
        help="Duration to record in seconds",
    ),
    voice_activity: bool = typer.Option(
        False,
        "--voice-activity",
        "-v",
        help="Record until silence is detected",
    ),
    silence_threshold: float = typer.Option(
        0.02,
        "--silence-threshold",
        help="Threshold for silence detection (0.0-1.0)",
        min=0.0,
        max=1.0,
    ),
    silence_duration: float = typer.Option(
        1.0,
        "--silence-duration",
        help="Silence duration to stop recording (seconds)",
        min=0.1,
    ),
    max_duration: float = typer.Option(
        60.0,
        "--max-duration",
        help="Maximum recording duration (seconds)",
        min=1.0,
    ),
    sample_rate: int = typer.Option(
        16000,
        "--sample-rate",
        "-r",
        help="Recording sample rate",
    ),
    channels: int = typer.Option(
        1,
        "--channels",
        "-c",
        help="Number of audio channels (1=mono, 2=stereo)",
        min=1,
        max=2,
    ),
    noise_reduction: bool = typer.Option(
        False,
        "--noise-reduction",
        "-n",
        help="Apply noise reduction",
    ),
    normalize: bool = typer.Option(
        False,
        "--normalize",
        help="Normalize audio volume",
    ),
    transcribe_after: bool = typer.Option(
        False,
        "--transcribe",
        "-t",
        help="Transcribe after recording",
    ),
    transcribe_model: str = typer.Option(
        "whisper",
        "--transcribe-model",
        help="STT model for transcription",
    ),
    play: bool = typer.Option(
        False,
        "--play",
        "-p",
        help="Play audio after recording",
    ),
):
    """Record audio from microphone."""
    try:
        # Initialize microphone
        try:
            microphone = Microphone(
                device_index=device,
                sample_rate=sample_rate,
                channels=channels,
                format="float32",
                chunk_size=1024,
            )
        except DependencyError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)

        # List of available devices for output
        devices = microphone.list_devices()
        if device is None:
            device_info = Microphone.get_default_device()
            device_name = device_info["name"] if device_info else "Default"
            console.print(f"[blue]Using input device:[/blue] {device_name}")
        else:
            device_name = next((d["name"] for d in devices if d["index"] == device), f"Device {device}")
            console.print(f"[blue]Using input device:[/blue] {device_name}")

        # Add audio processing filters if requested
        if noise_reduction:
            from fmus_vox.stream.microphone import NoiseReduction
            microphone.add_filter(NoiseReduction(strength=0.5))
            console.print("[blue]Noise reduction enabled[/blue]")

            # Calibrate noise profile
            console.print("[blue]Calibrating noise profile (please remain quiet)...[/blue]")
            microphone.calibrate_noise_profile(seconds=2.0)

        if normalize:
            from fmus_vox.stream.microphone import Normalization
            microphone.add_filter(Normalization(target_db=-3.0))
            console.print("[blue]Audio normalization enabled[/blue]")

        # Set up audio level visualization
        audio_levels = {"rms": 0.0, "peak": 0.0}

        def update_levels(levels):
            audio_levels["rms"] = levels["rms"]
            audio_levels["peak"] = levels["peak"]

        microphone.set_visualization_callback(update_levels)

        # Create a live display for the recording
        table = Table(show_header=False, box=None)
        table.add_column("Label", style="bold blue", width=16)
        table.add_column("Value")

        # Start recording
        with Live(table, refresh_per_second=10, console=console) as live:
            console.print("[bold blue]Recording...[/bold blue]")
            console.print("[blue]Press Ctrl+C to stop recording[/blue]")

            start_time = time.time()
            recording = None

            try:
                # Record audio
                if duration is not None:
                    # Record for fixed duration
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]Recording"),
                        BarColumn(),
                        TextColumn("[blue]{task.percentage:.0f}%"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Recording", total=duration)

                        # Update progress bar
                        def update_progress():
                            remaining = duration - (time.time() - start_time)
                            if remaining > 0:
                                progress.update(task, completed=duration - remaining)
                                return True
                            return False

                        # Start recording with visualization
                        recording = microphone.record(duration, update_levels)

                elif voice_activity:
                    # Record until silence
                    console.print("[blue]Recording until silence is detected...[/blue]")
                    recording = microphone.record_until_silence(
                        silence_threshold=silence_threshold,
                        silence_duration=silence_duration,
                        max_seconds=max_duration,
                        pre_buffer_seconds=0.5
                    )
                else:
                    # Manual recording mode
                    microphone.start_recording()

                    # Loop until Ctrl+C
                    while True:
                        # Update the live display
                        elapsed = time.time() - start_time
                        minutes, seconds = divmod(int(elapsed), 60)

                        # Clear and update table
                        table.rows = []
                        table.add_row("Recording time", f"{minutes:02d}:{seconds:02d}")

                        # Add audio level meter (text-based visualization)
                        rms_level = audio_levels["rms"]
                        peak_level = audio_levels["peak"]

                        rms_bar = '█' * int(rms_level * 20)
                        peak_bar = '█' * int(peak_level * 20)

                        table.add_row("Audio level", rms_bar)
                        table.add_row("Peak level", peak_bar)

                        # Sleep a bit to avoid hammering the CPU
                        time.sleep(0.1)

            except KeyboardInterrupt:
                if not duration and not voice_activity:
                    # Stop manual recording
                    console.print("\n[blue]Stopping recording...[/blue]")
                    recording = microphone.stop_recording()
            finally:
                microphone.close()

            # Calculate recording duration
            elapsed = time.time() - start_time
            minutes, seconds = divmod(int(elapsed), 60)
            console.print(f"[green]Recording finished:[/green] {minutes:02d}:{seconds:02d}")

            if recording and len(recording.data) > 0:
                # Save recording
                output_path = get_output_path(output)
                recording.save(output_path)
                console.print(f"[green]Audio saved to:[/green] {output_path}")

                # Transcribe if requested
                if transcribe_after:
                    console.print("[blue]Transcribing audio...[/blue]")
                    result = transcribe(recording, model=transcribe_model)
                    console.print(f"[green]Transcription:[/green] {result}")

                # Play if requested
                if play:
                    console.print("[blue]Playing audio...[/blue]")
                    recording.play()
            else:
                console.print("[yellow]Warning:[/yellow] No audio was recorded")

    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("play")
def play_cmd(
    input_path: Path = typer.Argument(
        ...,
        help="Path to input audio file",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    device: Optional[int] = typer.Option(
        None,
        "--device",
        "-d",
        help="Output device index (use 'devices' command to list)",
    ),
    loop: int = typer.Option(
        1,
        "--loop",
        "-l",
        help="Number of times to loop playback (0 for infinite)",
        min=0,
    ),
    equalizer: bool = typer.Option(
        False,
        "--equalizer",
        "-e",
        help="Apply equalizer effect",
    ),
    low_gain: float = typer.Option(
        0.0,
        "--low",
        help="Low frequency gain in dB (-12 to +12)",
        min=-12.0,
        max=12.0,
    ),
    mid_gain: float = typer.Option(
        0.0,
        "--mid",
        help="Mid frequency gain in dB (-12 to +12)",
        min=-12.0,
        max=12.0,
    ),
    high_gain: float = typer.Option(
        0.0,
        "--high",
        help="High frequency gain in dB (-12 to +12)",
        min=-12.0,
        max=12.0,
    ),
):
    """Play audio file."""
    try:
        # Load audio file
        console.print(f"[blue]Loading audio file:[/blue] {input_path}")
        audio = Audio.load(input_path)

        # Print audio info
        console.print(f"[blue]Audio info:[/blue] {audio.sample_rate}Hz, {audio.channels} channels, {audio.duration:.2f} seconds")

        # Initialize audio player
        try:
            player = AudioPlayer(
                device_index=device,
                sample_rate=audio.sample_rate,
                channels=audio.channels,
                format="float32",
            )
        except DependencyError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)

        # List of available devices for output
        if device is None:
            device_info = AudioPlayer.get_default_device()
            device_name = device_info["name"] if device_info else "Default"
            console.print(f"[blue]Using output device:[/blue] {device_name}")
        else:
            devices = AudioPlayer.list_devices()
            device_name = next((d["name"] for d in devices if d["index"] == device), f"Device {device}")
            console.print(f"[blue]Using output device:[/blue] {device_name}")

        # Add equalizer if requested
        if equalizer:
            from fmus_vox.stream.audioplayer import Equalizer
            eq = Equalizer({
                "low": low_gain,
                "mid": mid_gain,
                "high": high_gain
            })
            player.add_effect(eq)
            console.print(f"[blue]Equalizer enabled:[/blue] Low: {low_gain}dB, Mid: {mid_gain}dB, High: {high_gain}dB")

        # Create a live display for the playback
        table = Table(show_header=False, box=None)
        table.add_column("Label", style="bold blue", width=16)
        table.add_column("Value")

        # Set up playback progress callback
        position_sec = 0.0
        duration_sec = audio.duration

        def update_position(pos, dur):
            nonlocal position_sec
            position_sec = pos

        player.on_position_change(update_position)

        # Set up playback complete callback
        finished = False
        loop_count = 0

        def on_complete():
            nonlocal finished, loop_count
            loop_count += 1
            if loop == 0 or loop_count < loop:
                # Play again
                player.play(audio)
            else:
                finished = True

        player.on_playback_complete(on_complete)

        # Start playback
        console.print("[bold blue]Playing audio...[/bold blue]")
        console.print("[blue]Press Ctrl+C to stop playback[/blue]")

        # Start playback
        player.play(audio)

        # Monitor playback
        with Live(table, refresh_per_second=5, console=console) as live:
            try:
                while player.is_playing() or (loop > 0 and loop_count < loop) or (loop == 0):
                    if finished and loop > 0 and loop_count >= loop:
                        break

                    # Calculate time values
                    pos_min, pos_sec = divmod(int(position_sec), 60)
                    dur_min, dur_sec = divmod(int(duration_sec), 60)

                    # Create progress bar
                    progress_pct = position_sec / duration_sec if duration_sec > 0 else 0
                    progress_width = 30
                    filled = int(progress_pct * progress_width)
                    progress_bar = '█' * filled + '░' * (progress_width - filled)

                    # Update display
                    table.rows = []
                    table.add_row("Playback", f"{pos_min:02d}:{pos_sec:02d} / {dur_min:02d}:{dur_sec:02d}")
                    table.add_row("Progress", progress_bar)

                    if loop != 1:
                        table.add_row("Loop", f"{loop_count+1} of {loop if loop > 0 else '∞'}")

                    # Sleep a bit to avoid hammering the CPU
                    time.sleep(0.1)

            except KeyboardInterrupt:
                console.print("\n[blue]Stopping playback...[/blue]")
                player.stop()
            finally:
                player.close()

        console.print("[green]Playback finished[/green]")

    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("devices")
def devices_cmd(
    input_only: bool = typer.Option(
        False,
        "--input",
        "-i",
        help="Show only input devices",
    ),
    output_only: bool = typer.Option(
        False,
        "--output",
        "-o",
        help="Show only output devices",
    ),
):
    """List available audio devices."""
    try:
        # Create tables for devices
        if not output_only:
            input_table = Table(title="Input Devices (Microphones)")
            input_table.add_column("Index", style="cyan")
            input_table.add_column("Name")
            input_table.add_column("Channels", justify="right")
            input_table.add_column("Default", justify="center")

            # Get input devices
            try:
                input_devices = Microphone.list_devices()

                # Add devices to table
                for device in input_devices:
                    input_table.add_row(
                        str(device["index"]),
                        device["name"],
                        str(device["channels"]),
                        "✓" if device.get("default", False) else ""
                    )

                console.print(input_table)

            except DependencyError as e:
                console.print(f"[yellow]Could not list input devices:[/yellow] {str(e)}")

        if not input_only:
            output_table = Table(title="Output Devices (Speakers)")
            output_table.add_column("Index", style="cyan")
            output_table.add_column("Name")
            output_table.add_column("Channels", justify="right")
            output_table.add_column("Default", justify="center")

            # Get output devices
            try:
                output_devices = AudioPlayer.list_devices()

                # Add devices to table
                for device in output_devices:
                    output_table.add_row(
                        str(device["index"]),
                        device["name"],
                        str(device["channels"]),
                        "✓" if device.get("default", False) else ""
                    )

                console.print(output_table)

            except DependencyError as e:
                console.print(f"[yellow]Could not list output devices:[/yellow] {str(e)}")

    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("serve")
def serve_cmd(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        help="Host to bind the server to",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind the server to",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode",
    ),
):
    """Start API server."""
    try:
        console.print(f"[bold blue]Starting fmus-vox API server at:[/bold blue] http://{host}:{port}")

        # Start the API server
        api_serve(
            host=host,
            port=port,
            reload=reload,
            debug=debug,
        )

    except KeyboardInterrupt:
        console.print("\n[blue]Shutting down server[/blue]")
    except FmusVoxError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

@app.command("gui")
def gui_cmd():
    """Launch the GUI application."""
    try:
        # Import the GUI module
        try:
            from fmus_vox.gui import run_app
        except ImportError:
            console.print("[bold red]Error:[/bold red] GUI dependencies not installed.")
            console.print("Install with: pip install fmus-vox[gui]")
            sys.exit(1)

        console.print("[blue]Starting FMUS-VOX GUI application...[/blue]")

        # Run the GUI application
        run_app()

    except KeyboardInterrupt:
        console.print("\n[blue]Exiting GUI application[/blue]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        sys.exit(1)

# Run the app if the module is executed directly
if __name__ == "__main__":
    app()
