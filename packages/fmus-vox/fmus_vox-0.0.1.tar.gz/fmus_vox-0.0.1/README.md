# fmus-vox

A speech processing library for Python.

## About

fmus-vox is a Python library that provides a rich set of tools for audio processing, speech-to-text (STT), text-to-speech (TTS), voice cloning, wake word detection, and conversational AI.

## Features

- **Audio Processing**: Load, manipulate, and analyze audio with an intuitive interface
- **Speech-to-Text**: Transcribe speech with support for multiple models (Whisper, Wav2Vec, etc.)
- **Text-to-Speech**: Synthesize natural-sounding speech with various voices and styles
- **Voice Cloning**: Create synthetic speech that mimics a specific voice
- **Wake Word Detection**: Detect custom wake words in audio streams
- **Conversational AI**: Build voice-driven conversational agents
- **Streaming**: Real-time audio processing with low latency
- **API**: Easy integration with web applications

## Installation

### Basic Installation

```bash
pip install fmus-vox
```

### With Specific Features

```bash
# For speech-to-text capabilities
pip install fmus-vox[stt]

# For text-to-speech capabilities
pip install fmus-vox[tts]

# For voice cloning
pip install fmus-vox[voice]

# For API server
pip install fmus-vox[api]

# For all features
pip install fmus-vox[full]
```

## Usage Examples

### Audio Processing

```python
from fmus_vox import Audio

# Load and process audio
audio = Audio.load("recording.wav")
processed = audio.normalize().denoise().resample(target_sr=16000)
processed.save("processed.wav")

# Record audio
audio = Audio.record(seconds=5)
audio.save("recording.wav")
```

### Speech-to-Text

```python
from fmus_vox import transcribe

# Simple transcription
text = transcribe("recording.wav")
print(f"Transcription: {text}")

# With specific model and language
text = transcribe("recording.wav", model="whisper-large", language="en")
```

### Text-to-Speech

```python
from fmus_vox import speak

# Simple synthesis
speak("Hello, welcome to fmus-vox!", output="welcome.wav")

# With voice styling
from fmus_vox import Speaker

speaker = Speaker(voice="en-female-1")
speaker.set_style("happy").set_speed(1.2).speak("This is exciting!")
```

### Voice Cloning

```python
from fmus_vox import clone_voice

# Clone voice and synthesize speech
clone_voice("my_voice.wav", "Hello with my voice", output="cloned.wav")

# Advanced usage
from fmus_vox import VoiceCloner

cloner = VoiceCloner()
voice_id = cloner.add_reference("my_voice.wav")
audio = cloner.synthesize("Hello with my voice", voice_id)
audio.save("cloned.wav")
```

### Real-time Voice Application

```python
from fmus_vox import VoiceApp

app = VoiceApp()

@app.on_wake("hey assistant")
def wake_handler():
    print("Wake word detected!")
    return True  # Start listening

@app.on_transcribe
def transcribe_handler(text):
    print(f"User said: {text}")
    if "weather" in text.lower():
        return "Today's weather is sunny."
    return "I didn't understand that command."

app.run()
```

## License

MIT

## Contributing

Contributions are welcome! Please check out our [contributing guidelines](CONTRIBUTING.md).
