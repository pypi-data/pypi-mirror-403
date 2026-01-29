import os
import platform
import warnings
import logging
from typing import Generator
import numpy as np
from ltts.backends import TTSBackend

# Suppress warnings before importing kokoro
warnings.filterwarnings('ignore', category=SyntaxWarning)
warnings.filterwarnings('ignore', category=UserWarning, module=r'^jieba\._compat$')
warnings.filterwarnings('ignore', category=UserWarning, module=r'^torch\.nn\.modules\.rnn$')
warnings.filterwarnings('ignore', category=FutureWarning, module=r'^torch\.nn\.utils\.weight_norm$')

# Enable MPS fallback on macOS
if platform.system() == 'Darwin':
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

from kokoro import KPipeline  # noqa: E402
import jieba  # noqa: E402

# Suppress jieba loading messages
jieba.setLogLevel(logging.ERROR)


class KokoroBackend(TTSBackend):
    """Kokoro TTS backend implementation"""

    def __init__(self):
        self.pipeline = None
        self.current_lang_code = None

    def _get_lang_code_from_voice(self, voice: str) -> str:
        """Determine language code from voice prefix"""
        if voice.startswith('a'):
            return 'a'  # American English
        elif voice.startswith('b'):
            return 'b'  # British English
        elif voice.startswith('e'):
            return 'e'  # Spanish
        elif voice.startswith('f'):
            return 'f'  # French
        elif voice.startswith('h'):
            return 'h'  # Hindi
        elif voice.startswith('i'):
            return 'i'  # Italian
        elif voice.startswith('j'):
            return 'j'  # Japanese
        elif voice.startswith('p'):
            return 'p'  # Brazilian Portuguese
        elif voice.startswith('z'):
            return 'z'  # Mandarin Chinese
        return 'a'  # Default to American English

    def _ensure_unidic(self):
        """Download unidic dictionary if needed for Japanese"""
        try:
            import unidic
            from pathlib import Path
            import subprocess
            import sys
            if not Path(unidic.DICDIR).exists():
                print("Downloading Japanese dictionary (one-time setup)...")
                subprocess.run([sys.executable, '-m', 'unidic', 'download'], check=True)
        except ImportError:
            pass

    def _get_pipeline(self, lang_code: str = 'a'):
        """Get or create pipeline for the given language"""
        if self.pipeline is None or self.current_lang_code != lang_code:
            if lang_code == 'j':
                self._ensure_unidic()
            self.pipeline = KPipeline(lang_code=lang_code, repo_id='hexgrad/Kokoro-82M')
            self.current_lang_code = lang_code
        return self.pipeline

    def generate(self, text: str, voice: str = None, lang_code: str = None, **kwargs) -> Generator[np.ndarray, None, None]:
        """Generate audio from text using Kokoro TTS.

        Extra kwargs (ref_audio, ref_text, instruct) are ignored - they are
        Qwen-specific options passed through the unified interface.
        """
        if voice is None:
            voice = 'af_heart'
        if lang_code is None:
            lang_code = self._get_lang_code_from_voice(voice)

        pipeline = self._get_pipeline(lang_code)

        for gs, ps, audio in pipeline(text, voice=voice):
            yield audio

    def get_sample_rate(self) -> int:
        """Get the sample rate for Kokoro-generated audio"""
        return 24000

    def get_available_voices(self) -> dict:
        """Get dictionary of available voices"""
        return {
            'American English': ['af_heart', 'af_alloy', 'af_bella', 'af_nova', 'af_sarah', 'am_adam', 'am_michael'],
            'British English': ['bf_alice', 'bf_emma', 'bf_isabella', 'bm_daniel', 'bm_george'],
            'Japanese': ['jf_alpha', 'jm_kumo'],
            'Chinese': ['zf_xiaobei', 'zm_yunxi'],
            'Spanish': ['ef_dora', 'em_alex'],
            'French': ['ff_siwis'],
            'Hindi': ['hf_alpha', 'hm_omega'],
            'Italian': ['if_sara', 'im_nicola'],
            'Portuguese': ['pf_dora', 'pm_alex'],
        }
