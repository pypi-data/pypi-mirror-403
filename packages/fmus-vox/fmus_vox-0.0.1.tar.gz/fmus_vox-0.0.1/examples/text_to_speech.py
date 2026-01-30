#!/usr/bin/env python
"""
Text-to-Speech Example

This example demonstrates how to use fmus-vox to generate speech from text
with different voices and settings.
"""

import argparse
from pathlib import Path

from fmus_vox import speak, Speaker
from fmus_vox.core.errors import FmusVoxError


def simple_tts_example(text, output_path=None, voice="default", play=True):
    """
    Simple example using the functional API to generate speech.

    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file (optional)
        voice: Voice to use for synthesis
        play: Whether to play the audio
    """
    try:
        print(f"Converting text to speech using voice: {voice}")
        print(f"Text: \"{text}\"")

        # Generate speech
        audio = speak(text, voice=voice)

        print(f"Generated {audio.duration:.2f} seconds of audio")

        # Save if output path provided
        if output_path:
            audio.save(output_path)
            print(f"Audio saved to: {output_path}")

        # Play if requested
        if play:
            print("Playing audio...")
            audio.play()

        return audio

    except FmusVoxError as e:
        print(f"Error during text-to-speech: {e}")
        return None


def advanced_tts_example(text, output_path=None, voice="default",
                        model="vits", speed=1.0, play=True):
    """
    Advanced example using the Speaker class to customize TTS.

    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file (optional)
        voice: Voice to use for synthesis
        model: TTS model to use
        speed: Speaking speed (0.5-2.0)
        play: Whether to play the audio
    """
    try:
        print(f"Converting text to speech using:")
        print(f"  Model: {model}")
        print(f"  Voice: {voice}")
        print(f"  Speed: {speed}")
        print(f"Text: \"{text}\"")

        # Create speaker with specific model and voice
        speaker = Speaker(model=model, voice=voice)

        # Set speaking speed
        speaker.set_speed(speed)

        # Generate speech
        audio = speaker.speak(text)

        print(f"Generated {audio.duration:.2f} seconds of audio")

        # Save if output path provided
        if output_path:
            audio.save(output_path)
            print(f"Audio saved to: {output_path}")

        # Play if requested
        if play:
            print("Playing audio...")
            audio.play()

        return audio

    except FmusVoxError as e:
        print(f"Error during text-to-speech: {e}")
        return None


def list_available_voices():
    """List all available voices for TTS."""
    try:
        # Create a speaker
        speaker = Speaker()

        # Get available voices
        voices = speaker.get_available_voices()

        print(f"\nAvailable voices ({len(voices)}):")
        for voice in voices:
            print(f"  - {voice['id']}: {voice['name']} ({voice['language']})")

    except FmusVoxError as e:
        print(f"Error listing voices: {e}")


def main():
    """Run the text-to-speech example."""
    parser = argparse.ArgumentParser(description="Text-to-Speech Example")
    parser.add_argument("--text", "-t", default="Hello, welcome to the fmus-vox library! This is an example of text-to-speech synthesis.",
                       help="Text to synthesize")
    parser.add_argument("--output", "-o", help="Output audio file path")
    parser.add_argument("--voice", "-v", default="default", help="Voice to use")
    parser.add_argument("--model", "-m", default="vits", help="TTS model to use")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="Speaking speed (0.5-2.0)")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--advanced", "-a", action="store_true", help="Use advanced API")
    parser.add_argument("--no-play", action="store_true", help="Don't play the audio")

    args = parser.parse_args()

    # List voices if requested
    if args.list_voices:
        list_available_voices()
        return

    # Prepare output path if specified
    output_path = None
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate speech
    if args.advanced:
        advanced_tts_example(
            args.text,
            output_path=output_path,
            voice=args.voice,
            model=args.model,
            speed=args.speed,
            play=not args.no_play
        )
    else:
        simple_tts_example(
            args.text,
            output_path=output_path,
            voice=args.voice,
            play=not args.no_play
        )


if __name__ == "__main__":
    main()
