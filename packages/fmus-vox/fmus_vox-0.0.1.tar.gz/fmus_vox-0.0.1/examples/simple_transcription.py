#!/usr/bin/env python
"""
Simple Transcription Example

This example demonstrates how to transcribe audio files
using fmus-vox's transcription capabilities.
"""

import argparse
from pathlib import Path

from fmus_vox import Audio, transcribe
from fmus_vox.core.errors import FmusVoxError


def process_file(file_path, model="whisper", language=None, timestamps=False):
    """
    Process an audio file and transcribe it.

    Args:
        file_path: Path to the audio file
        model: STT model to use
        language: Optional language code
        timestamps: Whether to include timestamps
    """
    try:
        print(f"Loading audio file: {file_path}")
        audio = Audio.load(file_path)

        print(f"Audio duration: {audio.duration:.2f} seconds")
        print(f"Sample rate: {audio.sample_rate} Hz")
        print(f"Channels: {audio.channels}")

        # Normalize audio (optional but recommended)
        audio = audio.normalize()

        print(f"\nTranscribing with model: {model}")
        result = transcribe(
            audio,
            model=model,
            language=language,
            timestamps=timestamps
        )

        if timestamps:
            # Print transcript with timestamps
            print("\n--- Transcript with timestamps ---")
            for segment in result.segments:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                print(f"[{start:.2f}s - {end:.2f}s] {text}")
        else:
            # Print simple transcript
            print("\n--- Transcript ---")
            print(result.text)

        return result

    except FmusVoxError as e:
        print(f"Error during transcription: {e}")
        return None


def main():
    """Run the transcription example."""
    parser = argparse.ArgumentParser(description="Audio Transcription Example")
    parser.add_argument("audio_file", help="Path to audio file to transcribe")
    parser.add_argument("--model", default="whisper", help="STT model to use")
    parser.add_argument("--language", help="Language code (e.g., 'en', 'fr')")
    parser.add_argument("--timestamps", action="store_true", help="Include timestamps in output")
    parser.add_argument("--output", "-o", help="Save transcript to file")

    args = parser.parse_args()

    # Ensure the audio file exists
    file_path = Path(args.audio_file)
    if not file_path.exists():
        print(f"Error: Audio file '{file_path}' does not exist")
        return

    # Process the file
    result = process_file(
        file_path,
        model=args.model,
        language=args.language,
        timestamps=args.timestamps
    )

    # Save to output file if specified
    if result and args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.timestamps:
            # Write with timestamps
            with open(output_path, "w", encoding="utf-8") as f:
                for segment in result.segments:
                    start = segment["start"]
                    end = segment["end"]
                    text = segment["text"]
                    f.write(f"[{start:.2f}s - {end:.2f}s] {text}\n")
        else:
            # Write simple transcript
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.text)

        print(f"\nTranscript saved to: {output_path}")


if __name__ == "__main__":
    main()
