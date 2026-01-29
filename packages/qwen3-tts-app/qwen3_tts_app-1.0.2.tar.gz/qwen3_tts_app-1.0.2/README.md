# Qwen3TTS Python Client

Python client library for [Qwen3 TTS](https://qwen3-tts.app/) - Convert text to natural sounding audio with voice cloning and emotion control.

## Installation

```bash
pip install qwen3-tts-app
```

## Features

- Convert text to natural sounding audio in multiple languages
- Voice cloning and custom voice synthesis
- Emotion and tone control (happy, sad, excited, neutral)
- Real-time streaming synthesis
- Voice characteristic adjustment (speed, pitch, volume)

## Quick Start

```python
from qwen3tts import AudioArticulator, EmotionProfile

tts = AudioArticulator(api_key="your-api-key")

# Basic text-to-speech
audio = tts.render_speech("Hello from Qwen3 TTS!", voice_id="default")
audio.save_to_file("output.mp3")

# With emotion
audio = tts.render_speech(
    "This is exciting!",
    emotion=EmotionProfile.EXCITED,
    speed=1.2
)
audio.save_to_file("excited.mp3")
```

## Links

- [Service Website](https://qwen3-tts.app/)
- [Repository](https://github.com/wddaily/qwen3-tts)
- [PyPI Package](https://pypi.org/project/qwen3-tts-app/)

## License

MIT License
