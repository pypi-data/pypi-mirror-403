"""
Qwen3TTS - Python Client Library
Generated from https://qwen3-tts.app - Text-to-Speech synthesis service
This toolkit enables high-quality audio synthesis with voice cloning capabilities
"""

from qwen3tts.client import (
    AudioArticulator,
    AudioFormat,
    AudioMetadata,
    EmotionProfile,
    Qwen3TTSError,
    Qwen3TTSSync,
    SynthesizedAudio,
    VoiceConfiguration,
    articulate_text,
)

__version__ = "1.0.0"

__all__ = [
    "AudioArticulator",
    "AudioFormat",
    "AudioMetadata",
    "EmotionProfile",
    "Qwen3TTSError",
    "Qwen3TTSSync",
    "SynthesizedAudio",
    "VoiceConfiguration",
    "articulate_text",
]
