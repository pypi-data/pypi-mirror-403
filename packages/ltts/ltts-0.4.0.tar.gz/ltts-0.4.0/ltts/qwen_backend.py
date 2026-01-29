import hashlib
import os
import pickle
import platform
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
import numpy as np
from ltts.backends import TTSBackend


def _get_cache_dir() -> Path:
    """Get the ltts cache directory."""
    if platform.system() == 'Windows':
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    cache_dir = base / 'ltts' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _hash_file(file_path: str) -> str:
    """Compute SHA256 hash of a file's contents."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

# Enable MPS fallback on macOS
if platform.system() == 'Darwin':
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'


@contextmanager
def _suppress_output():
    """Suppress stdout/stderr at OS level (catches subprocess output too)."""
    try:
        stdout_fd = sys.stdout.fileno()
        stderr_fd = sys.stderr.fileno()
    except (AttributeError, OSError, ValueError):
        # stdout/stderr not backed by real file descriptors (e.g., in some IDEs)
        yield
        return

    saved_stdout = os.dup(stdout_fd)
    saved_stderr = os.dup(stderr_fd)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, stdout_fd)
        os.dup2(devnull, stderr_fd)
        yield
    finally:
        os.dup2(saved_stdout, stdout_fd)
        os.dup2(saved_stderr, stderr_fd)
        os.close(saved_stdout)
        os.close(saved_stderr)
        os.close(devnull)


def _import_qwen_tts():
    """Import qwen_tts while suppressing sox/flash-attn warnings."""
    import warnings
    with _suppress_output(), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from qwen_tts import Qwen3TTSModel
    return Qwen3TTSModel


class QwenTTSBackend(TTSBackend):
    """Qwen3-TTS backend implementation with preset voices and voice cloning support"""

    # Map language codes to Qwen language names
    LANGUAGE_MAP = {
        'zh': 'Chinese',
        'en': 'English',
        'ja': 'Japanese',
        'ko': 'Korean',
        'de': 'German',
        'fr': 'French',
        'ru': 'Russian',
        'pt': 'Portuguese',
        'es': 'Spanish',
        'it': 'Italian',
    }

    # Available preset voices for CustomVoice models
    PRESET_VOICES = {
        'Chinese': ['Vivian', 'Serena', 'Uncle_Fu', 'Dylan', 'Eric'],
        'English': ['Ryan', 'Aiden'],
        'Japanese': ['Ono_Anna'],
        'Korean': ['Sohee'],
    }

    # Default voice per language
    DEFAULT_VOICES = {
        'Chinese': 'Vivian',
        'English': 'Ryan',
        'Japanese': 'Ono_Anna',
        'Korean': 'Sohee',
    }

    def __init__(self, device: str = "cpu", model_size: str = "1.7B"):
        """
        Initialize Qwen3-TTS backend.

        Args:
            device: Device to use ('cpu', 'cuda', 'mps')
            model_size: Model size ('0.6B' or '1.7B')
        """
        self.device = device
        self.model_size = model_size
        self.model = None
        self.clone_model = None
        self._sample_rate = None

    def _get_device_map(self) -> str:
        """Get the device map string for model loading"""
        if self.device == 'cuda':
            return 'cuda:0'
        elif self.device == 'mps':
            return 'mps'
        return 'cpu'

    def _get_dtype(self):
        """Get the appropriate dtype for the device"""
        import torch
        if self.device == 'cpu':
            return torch.float32
        elif self.device == 'mps':
            return torch.float16  # MPS has limited bfloat16 support
        return torch.bfloat16

    def _get_attn_impl(self) -> Optional[str]:
        """Get attention implementation based on device"""
        if self.device == 'cuda':
            try:
                import flash_attn  # noqa: F401
                return 'flash_attention_2'
            except ImportError:
                pass
        return None

    def _get_model(self):
        """Lazy load the CustomVoice model"""
        if self.model is None:
            Qwen3TTSModel = _import_qwen_tts()
            model_name = f"Qwen/Qwen3-TTS-12Hz-{self.model_size}-CustomVoice"
            print(f"Loading Qwen3-TTS model: {model_name}...")

            kwargs = {
                'device_map': self._get_device_map(),
                'dtype': self._get_dtype(),
            }
            attn_impl = self._get_attn_impl()
            if attn_impl:
                kwargs['attn_implementation'] = attn_impl

            self.model = Qwen3TTSModel.from_pretrained(model_name, **kwargs)
        return self.model

    def _get_clone_model(self):
        """Lazy load the Base model for voice cloning"""
        if self.clone_model is None:
            Qwen3TTSModel = _import_qwen_tts()
            model_name = f"Qwen/Qwen3-TTS-12Hz-{self.model_size}-Base"
            print(f"Loading Qwen3-TTS clone model: {model_name}...")

            kwargs = {
                'device_map': self._get_device_map(),
                'dtype': self._get_dtype(),
            }
            attn_impl = self._get_attn_impl()
            if attn_impl:
                kwargs['attn_implementation'] = attn_impl

            self.clone_model = Qwen3TTSModel.from_pretrained(model_name, **kwargs)
        return self.clone_model

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character ranges"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return 'Chinese'
            elif '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff':
                return 'Japanese'
            elif '\uac00' <= char <= '\ud7af':
                return 'Korean'
        return 'English'

    def _get_language(self, lang_code: Optional[str], text: str) -> str:
        """Get language name from code or detect from text"""
        if lang_code and lang_code in self.LANGUAGE_MAP:
            return self.LANGUAGE_MAP[lang_code]
        return self._detect_language(text)

    def _get_voice_for_language(self, voice: Optional[str], language: str) -> str:
        """Get appropriate voice for the language"""
        if voice:
            # Check if voice is valid for any language
            for lang_voices in self.PRESET_VOICES.values():
                if voice in lang_voices:
                    return voice
            # Voice not found, use default
            print(f"Warning: Voice '{voice}' not found, using default for {language}")

        return self.DEFAULT_VOICES.get(language, 'Ryan')

    def generate(self, text: str, voice: str = None, lang_code: str = None,
                 ref_audio: Optional[str] = None, ref_text: str = "",
                 instruct: str = None, **kwargs) -> Generator[np.ndarray, None, None]:
        """
        Generate audio from text using Qwen3-TTS.

        Args:
            text: Text to convert to speech
            voice: Voice name (preset voice for CustomVoice model)
            lang_code: Language code (zh, en, ja, ko, de, fr, ru, pt, es, it)
            ref_audio: Reference audio file for voice cloning (uses Base model)
            ref_text: Reference text (transcript of the reference audio)
            instruct: Optional instruction for emotional/style control

        Yields:
            Audio chunks as numpy arrays
        """
        language = self._get_language(lang_code, text)

        if ref_audio:
            # Use voice cloning with Base model
            model = self._get_clone_model()

            # Check disk cache first, keyed by file content hash + ref_text
            file_hash = _hash_file(ref_audio)
            text_hash = hashlib.sha256(ref_text.encode()).hexdigest()[:16]
            cache_key = f"{file_hash}_{text_hash}"
            cache_file = _get_cache_dir() / f"voice_clone_{cache_key}.pkl"

            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    voice_clone_prompt = pickle.load(f)
            else:
                print("Extracting voice features...")
                voice_clone_prompt = model.create_voice_clone_prompt(
                    ref_audio=ref_audio,
                    ref_text=ref_text
                )
                with open(cache_file, 'wb') as f:
                    pickle.dump(voice_clone_prompt, f)

            wavs, sr = model.generate_voice_clone(
                text=text,
                language=language,
                voice_clone_prompt=voice_clone_prompt
            )
        else:
            # Use preset voices with CustomVoice model
            model = self._get_model()
            speaker = self._get_voice_for_language(voice, language)

            kwargs = {
                'text': text,
                'language': language,
                'speaker': speaker,
            }
            if instruct:
                kwargs['instruct'] = instruct

            wavs, sr = model.generate_custom_voice(**kwargs)

        self._sample_rate = sr

        # Yield the audio
        if isinstance(wavs, list):
            for wav in wavs:
                yield np.array(wav)
        else:
            yield np.array(wavs)

    def get_sample_rate(self) -> int:
        """Get the sample rate for Qwen3-TTS generated audio"""
        # Default sample rate if not yet generated
        return self._sample_rate or 24000

    def get_available_voices(self) -> dict:
        """Get dictionary of available preset voices by language"""
        return self.PRESET_VOICES.copy()
