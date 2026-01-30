"""
Helper functions for the CLI interface.

This module provides utility functions that support the CLI commands.
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from fmus_vox import Audio, transcribe, speak, VoiceStream, detect_wake_word, WakeWordDetector, chat


def get_output_path(path: Path) -> Path:
    """
    Ensure the output path exists and is valid.

    Args:
        path: The output path

    Returns:
        A valid Path object
    """
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def format_transcript(
    transcript: Union[str, Dict[str, Any]],
    timestamps: bool = False
) -> str:
    """
    Format transcription results for output.

    Args:
        transcript: Transcription result (str or dict with timestamps)
        timestamps: Whether to include timestamps in output

    Returns:
        Formatted transcript text
    """
    if isinstance(transcript, str):
        return transcript

    if not timestamps:
        return transcript.get("text", "")

    # Format with timestamps
    segments = transcript.get("segments", [])
    if not segments:
        return transcript.get("text", "")

    lines = []
    for segment in segments:
        start = format_timestamp(segment.get("start", 0))
        end = format_timestamp(segment.get("end", 0))
        text = segment.get("text", "").strip()
        lines.append(f"[{start} --> {end}] {text}")

    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as HH:MM:SS.mmm.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def interactive_mode(
    wake_word: str,
    stt_model: str,
    tts_model: str,
    language: Optional[str],
    voice: str,
    console: Console,
) -> None:
    """
    Run interactive voice mode with wake word detection.

    Args:
        wake_word: Wake word to trigger interaction
        stt_model: STT model to use
        tts_model: TTS model to use
        language: Language code
        voice: TTS voice to use
        console: Rich console for output
    """
    # Set up wake word detector
    detector = WakeWordDetector()
    detector.add_keyword(wake_word)

    # Set up voice stream
    stream = VoiceStream()

    # Set up conversation context
    context = {"history": []}

    def on_wake_word(audio, metadata):
        """Handle wake word detection."""
        console.print(f"[cyan]Wake word detected![/cyan]")
        console.print("[cyan]Listening...[/cyan]")

        # Start recording speech
        speech = stream.record_until_silence(max_seconds=10)
        if speech.duration < 0.5:
            console.print("[yellow]Speech too short, ignoring[/yellow]")
            return

        # Transcribe speech
        console.print("[blue]Transcribing...[/blue]")
        user_text = transcribe(speech, model=stt_model, language=language)
        console.print(f"[green]You said:[/green] {user_text}")

        # Generate response
        console.print("[blue]Generating response...[/blue]")
        assistant_text = chat(user_text, context=context)
        context["history"].append({"user": user_text, "assistant": assistant_text})

        # Render response in markdown
        console.print(Panel(Markdown(assistant_text), title="Response"))

        # Synthesize response
        console.print("[blue]Speaking response...[/blue]")
        audio = speak(assistant_text, model=tts_model, voice=voice)
        audio.play()

    # Start listening for wake word
    console.print(f"[bold blue]Listening for wake word:[/bold blue] '{wake_word}'")
    detector.listen(on_detection=on_wake_word, continuous=True)


def run_benchmark(
    func: callable,
    name: str,
    iterations: int = 5,
    console: Optional[Console] = None,
) -> Dict[str, float]:
    """
    Run benchmark on a function.

    Args:
        func: Function to benchmark
        name: Name of the benchmark
        iterations: Number of iterations
        console: Optional console for output

    Returns:
        Dictionary with benchmark results
    """
    if console is None:
        console = Console()

    console.print(f"[bold blue]Running benchmark:[/bold blue] {name}")

    times = []
    for i in range(iterations):
        console.print(f"  Iteration {i+1}/{iterations}...")
        start = time.time()
        func()
        end = time.time()
        elapsed = end - start
        times.append(elapsed)
        console.print(f"    [green]{elapsed:.4f}s[/green]")

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    results = {
        "name": name,
        "average": avg_time,
        "min": min_time,
        "max": max_time,
        "iterations": iterations,
    }

    console.print(f"[bold green]Results:[/bold green] avg={avg_time:.4f}s, min={min_time:.4f}s, max={max_time:.4f}s")

    return results
