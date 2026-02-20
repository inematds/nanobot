"""Voice transcription providers: Groq, OpenAI Whisper, and local Whisper."""

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from loguru import logger

if TYPE_CHECKING:
    from nanobot.config.schema import Config


class GroqTranscriptionProvider:
    """
    Voice transcription provider using Groq's Whisper API.

    Groq offers extremely fast transcription with a generous free tier.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/audio/transcriptions"

    async def transcribe(self, file_path: str | Path) -> str:
        """
        Transcribe an audio file using Groq.

        Args:
            file_path: Path to the audio file.

        Returns:
            Transcribed text.
        """
        if not self.api_key:
            logger.warning("Groq API key not configured for transcription")
            return ""

        path = Path(file_path)
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return ""

        try:
            async with httpx.AsyncClient() as client:
                with open(path, "rb") as f:
                    files = {
                        "file": (path.name, f),
                        "model": (None, "whisper-large-v3"),
                    }
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                    }

                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        files=files,
                        timeout=60.0
                    )

                    response.raise_for_status()
                    data = response.json()
                    return data.get("text", "")

        except Exception as e:
            logger.error(f"Groq transcription error: {e}")
            return ""


class OpenAIWhisperProvider:
    """
    Voice transcription provider using OpenAI Whisper API.

    Requires OPENAI_API_KEY or openai.api_key in config.
    Uses model whisper-1 by default.
    """

    def __init__(self, api_key: str | None = None, model: str = "whisper-1", language: str = ""):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or "whisper-1"
        self.language = language
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, file_path: str | Path) -> str:
        """Transcribe an audio file using the OpenAI Whisper API."""
        if not self.api_key:
            logger.warning("OpenAI API key not configured for transcription")
            return ""

        path = Path(file_path)
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return ""

        try:
            async with httpx.AsyncClient() as client:
                with open(path, "rb") as f:
                    files: dict = {
                        "file": (path.name, f),
                        "model": (None, self.model),
                    }
                    if self.language:
                        files["language"] = (None, self.language)

                    headers = {"Authorization": f"Bearer {self.api_key}"}

                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        files=files,
                        timeout=120.0,
                    )

                    response.raise_for_status()
                    data = response.json()
                    return data.get("text", "").strip()

        except Exception as e:
            logger.error(f"OpenAI Whisper transcription error: {e}")
            return ""


class LocalWhisperProvider:
    """
    Local Whisper transcription using the openai-whisper Python package.

    Runs entirely offline — no API key required.
    Requires: pip install openai-whisper  (and ffmpeg in PATH)

    Available models (size vs accuracy trade-off):
      tiny, base, small, medium, large, large-v2, large-v3
    """

    def __init__(self, model: str = "base", language: str = ""):
        self.model_name = model or "base"
        self.language = language or None
        self._model = None  # Lazy-loaded on first use

    async def transcribe(self, file_path: str | Path) -> str:
        """Transcribe an audio file using a local Whisper model."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return ""

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._transcribe_sync, str(path))
        except Exception as e:
            logger.error(f"Local Whisper transcription error: {e}")
            return ""

    def _transcribe_sync(self, file_path: str) -> str:
        """Synchronous transcription (runs in a thread pool executor)."""
        try:
            import whisper  # type: ignore[import]
        except ImportError:
            logger.error(
                "openai-whisper not installed. "
                "Run: pip install openai-whisper  (and install ffmpeg)"
            )
            return ""

        if self._model is None:
            logger.info(f"Loading local Whisper model '{self.model_name}' (first run may be slow)...")
            self._model = whisper.load_model(self.model_name)
            logger.info(f"Whisper model '{self.model_name}' ready")

        result = self._model.transcribe(file_path, language=self.language)
        return result.get("text", "").strip()


def create_transcription_provider(config: "Config"):
    """
    Factory: create the configured transcription provider.

    Config key: transcription.provider  ("groq" | "openai" | "local")
    """
    provider_name = config.transcription.provider
    model = config.transcription.model
    language = config.transcription.language

    if provider_name == "local":
        logger.info(f"Transcription: local Whisper (model={model or 'base'})")
        return LocalWhisperProvider(model=model or "base", language=language)

    if provider_name == "openai":
        logger.info(f"Transcription: OpenAI Whisper API (model={model or 'whisper-1'})")
        return OpenAIWhisperProvider(
            api_key=config.providers.openai.api_key,
            model=model or "whisper-1",
            language=language,
        )

    # Default: groq
    logger.info("Transcription: Groq Whisper API")
    return GroqTranscriptionProvider(api_key=config.providers.groq.api_key)
