#!/usr/bin/env python
"""
Voice Assistant Example

This example demonstrates a complete voice assistant using fmus-vox,
combining wake word detection, speech recognition, and text-to-speech.
"""

import os
import asyncio
import argparse
from typing import Optional

from fmus_vox.wakeword import create_detector
from fmus_vox.stream import VoiceStream
from fmus_vox.stt import transcribe
from fmus_vox.tts import speak
from fmus_vox.chatbot import Conversation, OpenAIProvider


class VoiceAssistant:
    """
    Simple voice assistant that listens for a wake word, transcribes speech,
    processes it with a language model, and speaks the response.
    """

    def __init__(
        self,
        wake_word: str = "hey assistant",
        wake_word_model: str = "porcupine",
        wake_word_threshold: float = 0.5,
        openai_api_key: Optional[str] = None,
        system_prompt: str = "You are a helpful voice assistant. Keep responses short and direct."
    ):
        """
        Initialize the voice assistant.

        Args:
            wake_word: Wake word to listen for.
            wake_word_model: Type of wake word model to use ('porcupine' or 'precise').
            wake_word_threshold: Detection threshold for the wake word.
            openai_api_key: OpenAI API key for conversation. If None, uses OPENAI_API_KEY env var.
            system_prompt: System prompt for the conversation context.
        """
        # Get OpenAI API key
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Provide it as parameter or set OPENAI_API_KEY env var.")

        # Create LLM provider and conversation
        self.llm_provider = OpenAIProvider(api_key=self.openai_api_key)
        self.conversation = Conversation(system_prompt=system_prompt, llm_provider=self.llm_provider)

        # Set up wake word detector
        self.wake_word = wake_word
        self.wake_detector = create_detector(
            wake_word=wake_word,
            threshold=wake_word_threshold,
            model_type=wake_word_model
        )

        # Set up voice stream
        self.voice_stream = VoiceStream(
            vad_mode="normal",
            min_silence_duration=0.8,
            min_speech_duration=0.5
        )

        # State variables
        self.is_listening = False
        self.is_running = False

    def on_wake_word(self, metadata):
        """Callback when wake word is detected."""
        if not self.is_listening:
            print(f"🎤 Wake word detected: {metadata['wake_word']}")
            print("Listening...")
            self.is_listening = True

    def on_speech(self, audio, metadata):
        """Callback when speech is detected."""
        if self.is_listening:
            # Only process speech if we're in listening mode (after wake word)
            duration = metadata.get("duration", 0)

            if duration < 1.0:
                # Ignore very short utterances
                print("Speech too short, ignoring.")
                self.is_listening = False
                return

            print(f"Processing speech ({duration:.1f}s)...")

            # Transcribe the speech
            transcription = transcribe(audio)
            if not transcription.strip():
                print("No speech detected.")
                self.is_listening = False
                return

            print(f"You: {transcription}")

            # Get response from the conversation
            asyncio.create_task(self.process_input(transcription, audio))

    async def process_input(self, text, audio):
        """Process user input and generate a response."""
        # Add the user message and generate a response
        response = await self.conversation.generate_response(text, audio=audio)

        print(f"Assistant: {response.content}")

        # Speak the response
        audio = speak(response.content)
        audio.play()

        # Reset listening state
        self.is_listening = False

    def start(self):
        """Start the voice assistant."""
        if self.is_running:
            return

        self.is_running = True

        # Register callback for wake word detection
        self.wake_detector.add_callback(self.wake_word, self.on_wake_word)

        # Register callback for speech detection
        self.voice_stream.on_speech(self.on_speech)

        # Start the voice stream
        self.voice_stream.start()

        # Start wake word detection
        self.wake_detector.start_streaming(self.voice_stream.microphone)

        print(f"🎧 Voice assistant started. Say '{self.wake_word}' to activate.")

    def stop(self):
        """Stop the voice assistant."""
        if not self.is_running:
            return

        self.is_running = False
        self.is_listening = False

        # Stop wake word detection
        self.wake_detector.stop_streaming()

        # Stop the voice stream
        self.voice_stream.stop()

        print("Voice assistant stopped.")


def main():
    """Run the voice assistant example."""
    parser = argparse.ArgumentParser(description="Voice Assistant Example")
    parser.add_argument("--wake-word", default="hey assistant", help="Wake word to use")
    parser.add_argument("--model", default="porcupine", choices=["porcupine", "precise"],
                        help="Wake word detection model")
    parser.add_argument("--threshold", type=float, default=0.5, help="Wake word detection threshold")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")

    args = parser.parse_args()

    # Create and start the voice assistant
    assistant = VoiceAssistant(
        wake_word=args.wake_word,
        wake_word_model=args.model,
        wake_word_threshold=args.threshold,
        openai_api_key=args.api_key
    )

    try:
        assistant.start()

        # Keep the program running
        while assistant.is_running:
            asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping voice assistant...")
    finally:
        assistant.stop()


if __name__ == "__main__":
    main()
