from abc import ABC, abstractmethod
from typing import Generator, Tuple
import numpy as np

class TTSBackend(ABC):
    """Abstract base class for TTS backends"""

    @abstractmethod
    def generate(self, text: str, voice: str = None, lang_code: str = None, **kwargs) -> Generator[np.ndarray, None, None]:
        """
        Generate audio from text.

        Args:
            text: Text to convert to speech
            voice: Voice identifier
            lang_code: Optional language code
            **kwargs: Backend-specific options (e.g., ref_audio, instruct)

        Yields:
            Audio chunks as numpy arrays
        """
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        """Get the sample rate for generated audio"""
        pass

    @abstractmethod
    def get_available_voices(self) -> dict:
        """Get dictionary of available voices by language"""
        pass
