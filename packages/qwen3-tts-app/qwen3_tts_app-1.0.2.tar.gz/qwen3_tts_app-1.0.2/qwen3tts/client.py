"""
Qwen3TTS - Python Client Library
Generated from https://qwen3-tts.app - Text-to-Speech synthesis service
This toolkit enables high-quality audio synthesis with voice cloning capabilities
"""

import asyncio
import base64
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional, List
from urllib.parse import urljoin

import httpx


class EmotionProfile(str, Enum):
    """Emotional tone profiles for expressive speech synthesis"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    SERIOUS = "serious"


class AudioFormat(str, Enum):
    """Supported audio output formats"""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"


@dataclass
class VoiceConfiguration:
    """Voice synthesis parameters"""
    speed: float = 1.0      # Speech rate: 0.5 to 2.0
    pitch: float = 1.0      # Pitch adjustment: 0.5 to 2.0
    volume: float = 0.9     # Volume: 0.0 to 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "speed": self.speed,
            "pitch": self.pitch,
            "volume": self.volume
        }


@dataclass
class AudioMetadata:
    """Metadata about synthesized audio"""
    format: str
    size_bytes: int
    sample_rate: int = 24000
    channels: int = 1
    duration_seconds: float = 0.0


@dataclass
class SynthesizedAudio:
    """Result of text-to-speech synthesis"""
    data: bytes
    metadata: AudioMetadata

    def save_to_file(self, filepath: str | Path) -> None:
        """Save audio data to file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(self.data)

    def to_base64(self) -> str:
        """Convert audio to base64 encoded string"""
        return base64.b64encode(self.data).decode('utf-8')

    def to_data_uri(self) -> str:
        """Generate data URI for embedding in HTML/audio players"""
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime = mime_types.get(self.metadata.format, "audio/mpeg")
        b64 = self.to_base64()
        return f"data:{mime};base64,{b64}"

    def formatted_size(self) -> str:
        """Get human-readable file size"""
        size = self.metadata.size_bytes
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} GB"


class AudioArticulator:
    """
    Main Qwen3 TTS Python client
    Provides text-to-speech synthesis with emotion and voice control
    """

    DEFAULT_API_ENDPOINT = "https://api.qwen3-tts.app/v1/synthesize"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str,
        endpoint: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT
    ):
        """
        Initialize the Qwen3 TTS client

        Args:
            api_key: Your Qwen3 TTS API key
            endpoint: Custom API endpoint (optional)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint or self.DEFAULT_API_ENDPOINT
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def render_speech(
        self,
        text: str,
        voice_id: str = "default",
        emotion: EmotionProfile = EmotionProfile.NEUTRAL,
        config: Optional[VoiceConfiguration] = None,
        output_format: AudioFormat = AudioFormat.MP3,
        language: str = "en"
    ) -> SynthesizedAudio:
        """
        Convert text to speech with full parameter control

        Args:
            text: Input text to synthesize
            voice_id: Voice profile identifier
            emotion: Emotional tone for speech
            config: Voice configuration (speed, pitch, volume)
            output_format: Desired audio format
            language: Language code (en, zh, ja, etc.)

        Returns:
            SynthesizedAudio object containing audio data and metadata
        """
        if config is None:
            config = VoiceConfiguration()

        request_payload = {
            "text": text,
            "voice_id": voice_id,
            "language": language,
            "emotion": emotion.value,
            "output_format": output_format.value,
            "config": config.to_dict()
        }

        client = self._get_client()
        response = await client.post(
            self.endpoint,
            json=request_payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "qwen3-tts-app-python/1.0",
                "Content-Type": "application/json"
            }
        )

        if response.status_code != 200:
            error_text = response.text
            raise Qwen3TTSError(f"API error ({response.status_code}): {error_text}")

        audio_data = response.content

        return SynthesizedAudio(
            data=audio_data,
            metadata=AudioMetadata(
                format=output_format.value,
                size_bytes=len(audio_data),
                sample_rate=24000,
                channels=1
            )
        )

    async def articulate_batch(
        self,
        texts: List[str],
        voice_id: str = "default",
        config: Optional[VoiceConfiguration] = None,
    ) -> List[SynthesizedAudio]:
        """
        Convert multiple texts to audio efficiently

        Args:
            texts: List of text strings to synthesize
            voice_id: Voice profile identifier
            config: Voice configuration

        Returns:
            List of SynthesizedAudio objects
        """
        results = []
        for i, text in enumerate(texts):
            audio = await self.render_speech(text, voice_id=voice_id, config=config)
            results.append(audio)
        return results

    async def clone_voice_profile(
        self,
        name: str,
        sample_urls: List[str],
        description: Optional[str] = None
    ) -> str:
        """
        Create a custom voice profile from audio samples

        Args:
            name: Name for the new voice profile
            sample_urls: URLs of audio samples for cloning
            description: Optional description

        Returns:
            Voice ID of the newly created profile
        """
        clone_endpoint = urljoin(self.endpoint, "/voice-clone")

        payload = {
            "name": name,
            "sample_urls": sample_urls,
            "description": description or ""
        }

        client = self._get_client()
        response = await client.post(
            clone_endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "qwen3-tts-app-python/1.0",
                "Content-Type": "application/json"
            }
        )

        if response.status_code != 200:
            raise Qwen3TTSError(f"Voice clone failed: {response.text}")

        data = response.json()
        return data.get("voice_id", "")

    async def enumerate_voices(self) -> List[dict[str, Any]]:
        """
        Retrieve available voice profiles

        Returns:
            List of voice profile information dictionaries
        """
        voices_endpoint = urljoin(self.endpoint, "/voices")
        client = self._get_client()

        response = await client.get(
            voices_endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "qwen3-tts-app-python/1.0"
            }
        )

        if response.status_code != 200:
            raise Qwen3TTSError(f"Failed to list voices: {response.text}")

        return response.json()

    async def convert_audio_format(
        self,
        audio_data: bytes,
        target_format: AudioFormat
    ) -> SynthesizedAudio:
        """
        Convert audio between formats

        Args:
            audio_data: Input audio bytes
            target_format: Desired output format

        Returns:
            New SynthesizedAudio with converted data
        """
        # In a real implementation, this would use audio conversion libraries
        # For now, we return a placeholder
        return SynthesizedAudio(
            data=audio_data,
            metadata=AudioMetadata(
                format=target_format.value,
                size_bytes=len(audio_data)
            )
        )


class Qwen3TTSError(Exception):
    """Exception raised for Qwen3 TTS API errors"""
    pass


# Synchronous wrapper for convenience
class Qwen3TTSSync:
    """Synchronous wrapper for AudioArticulator"""

    def __init__(self, api_key: str, endpoint: Optional[str] = None):
        self._async_client = AudioArticulator(api_key, endpoint)

    def render_speech(
        self,
        text: str,
        voice_id: str = "default",
        emotion: EmotionProfile = EmotionProfile.NEUTRAL,
        config: Optional[VoiceConfiguration] = None,
        output_format: AudioFormat = AudioFormat.MP3,
        language: str = "en"
    ) -> SynthesizedAudio:
        """Synchronous version of render_speech"""
        return asyncio.run(self._async_client.render_speech(
            text, voice_id, emotion, config, output_format, language
        ))


# Convenience function
def articulate_text(
    text: str,
    api_key: str,
    emotion: EmotionProfile = EmotionProfile.NEUTRAL,
    output_path: Optional[str] = None
) -> SynthesizedAudio:
    """
    Quick text-to-speech conversion

    Args:
        text: Input text
        api_key: Qwen3 TTS API key
        emotion: Emotional tone
        output_path: Optional file path to save audio

    Returns:
        SynthesizedAudio object
    """
    tts = Qwen3TTSSync(api_key)
    audio = tts.render_speech(text, emotion=emotion)
    if output_path:
        audio.save_to_file(output_path)
    return audio


# Example usage
async def main():
    """Example demonstrating Qwen3 TTS Python client usage"""
    api_key = os.getenv("QWEN3_API_KEY", "your-api-key")

    async with AudioArticulator(api_key) as tts:
        # Basic text-to-speech
        audio1 = await tts.render_speech(
            "Hello from Qwen3 TTS Python client!",
            voice_id="default"
        )
        audio1.save_to_file("hello.mp3")
        print(f"Audio saved: {audio1.formatted_size()}")

        # Emotional speech
        audio2 = await tts.render_speech(
            "This is exciting news from Qwen3!",
            emotion=EmotionProfile.EXCITED,
            config=VoiceConfiguration(speed=1.2, pitch=1.1)
        )
        audio2.save_to_file("excited.mp3")
        print("Emotional audio saved!")

        # Batch processing
        texts = [
            "First sentence of the batch.",
            "Second sentence of the batch.",
            "Third sentence of the batch."
        ]
        batch_audio = await tts.articulate_batch(texts)
        for i, audio in enumerate(batch_audio):
            audio.save_to_file(f"batch_{i}.mp3")
        print(f"Batch processing complete: {len(batch_audio)} files")


if __name__ == "__main__":
    asyncio.run(main())
