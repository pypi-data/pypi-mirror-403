import argparse
import os
import shutil
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd


def _get_cache_dir() -> Path:
    """Get the ltts cache directory."""
    import platform
    if platform.system() == 'Windows':
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return base / 'ltts' / 'cache'


def clear_cache():
    """Clear the voice clone cache."""
    cache_dir = _get_cache_dir()
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"Cleared cache: {cache_dir}")
    else:
        print("Cache is already empty")

# Global backend instance cache
_backend_cache = {}

def get_backend(backend_name: str = 'qwen', device: str = 'cpu', model_size: str = '1.7B'):
    """Get or create the TTS backend"""
    cache_key = (backend_name, device, model_size)
    if cache_key not in _backend_cache:
        if backend_name == 'kokoro':
            from ltts.kokoro_backend import KokoroBackend
            _backend_cache[cache_key] = KokoroBackend()
        elif backend_name == 'qwen':
            from ltts.qwen_backend import QwenTTSBackend
            _backend_cache[cache_key] = QwenTTSBackend(device=device, model_size=model_size)
        else:
            raise ValueError(f"Unknown backend: {backend_name}")
    return _backend_cache[cache_key]

def _generate_audio(backend_instance, text, voice, lang_code,
                    ref_audio, ref_text, instruct):
    """Generate audio chunks from the backend."""
    return list(backend_instance.generate(
        text, voice, lang_code,
        ref_audio=ref_audio, ref_text=ref_text, instruct=instruct
    ))


def text_to_speech(text, output_path, voice=None, lang_code=None,
                   backend_name='qwen', device='cpu', ref_audio=None, ref_text="",
                   model_size='1.7B', instruct=None):
    """Convert text to speech and save as audio file"""
    backend_instance = get_backend(backend_name, device, model_size)
    audio_chunks = _generate_audio(backend_instance, text, voice,
                                   lang_code, ref_audio, ref_text, instruct)
    full_audio = np.concatenate(audio_chunks)

    # Get sample rate from backend
    sample_rate = backend_instance.get_sample_rate()

    # Detect format from extension, default to MP3
    path_str = str(output_path)
    if path_str.endswith('.ogg'):
        sf.write(path_str, full_audio, sample_rate, format='OGG')
    elif path_str.endswith('.flac'):
        sf.write(path_str, full_audio, sample_rate, format='FLAC')
    elif path_str.endswith('.wav'):
        sf.write(path_str, full_audio, sample_rate, format='WAV')
    else:
        # Default to MP3
        sf.write(path_str, full_audio, sample_rate, format='MP3')

    return output_path

def speak(text, voice=None, lang_code=None, stream=False,
          backend_name='qwen', device='cpu', ref_audio=None, ref_text="",
          model_size='1.7B', instruct=None):
    """Play generated speech through the system audio output."""
    backend_instance = get_backend(backend_name, device, model_size)

    if stream and backend_name == 'kokoro':
        # Streaming only supported for Kokoro
        sample_rate = backend_instance.get_sample_rate()
        first_chunk = True
        for audio in backend_instance.generate(text, voice, lang_code):
            if first_chunk:
                print("Speaking...")
                first_chunk = False
            sd.play(audio, samplerate=sample_rate)
            sd.wait()
    else:
        if stream and backend_name != 'kokoro':
            print(f"Warning: --chunk streaming is only supported with Kokoro backend, ignoring")
        print("Preparing audio...")
        audio_chunks = _generate_audio(backend_instance, text, voice,
                                       lang_code, ref_audio, ref_text, instruct)
        full_audio = np.concatenate(audio_chunks)
        sample_rate = backend_instance.get_sample_rate()
        print("Speaking...")
        sd.play(full_audio, samplerate=sample_rate)
        sd.wait()

def main():
    parser = argparse.ArgumentParser(
        description='Convert text to speech using Qwen3-TTS (default) or Kokoro TTS',
        epilog='''
Qwen3-TTS backend (default):
  Supports 10 languages with preset voices or voice cloning
  Preset voices (use -v/--voice):
    Chinese: Vivian, Serena, Uncle_Fu, Dylan, Eric
    English: Ryan, Aiden
    Japanese: Ono_Anna
    Korean: Sohee
  Voice cloning: Use --ref-audio with optional --ref-text
  Emotional control: Use --instruct "speak with excitement"
  Language codes (-l): zh, en, ja, ko, de, fr, ru, pt, es, it
  Model sizes (--model-size): 0.6B (faster), 1.7B (better quality, default)
  Example: ltts "Hello world" -v Ryan
  Example: ltts "Hello world" --ref-audio voice.wav

Kokoro TTS backend:
  American English: af_heart, af_alloy, af_bella, af_nova, af_sarah, am_adam, am_michael, etc.
  British English: bf_alice, bf_emma, bf_isabella, bm_daniel, bm_george, etc.
  Japanese: jf_alpha, jm_kumo
  Chinese: zf_xiaobei, zm_yunxi
  Spanish: ef_dora, em_alex
  French: ff_siwis
  Hindi: hf_alpha, hm_omega
  Italian: if_sara, im_nicola
  Portuguese: pf_dora, pm_alex
  Full voice list: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

Language codes (for -l flag):
  Kokoro: a=American English, b=British English, e=Spanish, f=French, h=Hindi,
          i=Italian, j=Japanese, p=Portuguese, z=Chinese
  Qwen3-TTS: zh=Chinese, en=English, ja=Japanese, ko=Korean, de=German,
             fr=French, ru=Russian, pt=Portuguese, es=Spanish, it=Italian
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('text', nargs='?', help='Text to convert to speech (reads from stdin if omitted and piped)')
    parser.add_argument('-o', '--output', help='Output audio file path (default: output.mp3). Ignored when using --say',
                       default='output.mp3')
    parser.add_argument('-v', '--voice', help='Voice to use (Qwen3-TTS preset voices or Kokoro voices)',
                       default=None)
    parser.add_argument('-l', '--lang', help='Language code (see --help for codes per backend)',
                       default=None)
    parser.add_argument('-s', '--say', action='store_true', help='Play audio through speakers instead of writing a file (ignores -o/--output)')
    parser.add_argument('-c', '--chunk', action='store_true', help='Stream audio chunks as they are generated for faster initial playback (use with -s/--say). Only works with Kokoro backend')
    parser.add_argument('-b', '--backend', choices=['qwen', 'kokoro'], default='qwen',
                       help='TTS backend to use (default: qwen)')
    parser.add_argument('-d', '--device', choices=['cpu', 'cuda', 'mps'], default='cpu',
                       help='Device to use for inference (default: cpu)')
    parser.add_argument('--ref-audio', help='Reference audio file for voice cloning (3+ seconds recommended)')
    parser.add_argument('--ref-text', default='', help='Reference text (transcript of reference audio) for voice cloning')
    parser.add_argument('--model-size', choices=['0.6B', '1.7B'], default='1.7B',
                       help='Model size for Qwen3-TTS (default: 1.7B)')
    parser.add_argument('--instruct', help='Instruction for emotional/style control (Qwen3-TTS only, e.g., "speak with excitement")')
    parser.add_argument('--clear-cache', action='store_true', help='Clear the voice clone cache and exit')

    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()
        return

    # Validate backend-specific requirements
    if args.backend == 'kokoro' and not args.voice:
        args.voice = 'af_heart'  # Default Kokoro voice
    if args.backend == 'qwen' and not args.voice and not args.ref_audio:
        args.voice = 'Ryan'  # Default Qwen voice

    # Resolve text from arg or stdin when piped
    input_text = args.text
    if input_text is None and not sys.stdin.isatty():
        input_text = sys.stdin.read().rstrip('\n')
    if not input_text:
        parser.error('No text provided. Pass TEXT or pipe input to stdin.')

    if args.say:
        try:
            speak(input_text, args.voice, args.lang, args.chunk,
                  args.backend, args.device, args.ref_audio, args.ref_text,
                  args.model_size, args.instruct)
        except Exception as e:
            print(f"Audio playback failed: {e}")
            return
        print("✓ Done")
        return
    output_path = Path(args.output)
    print("Generating speech...")
    result = text_to_speech(input_text, output_path, args.voice, args.lang,
                           args.backend, args.device, args.ref_audio, args.ref_text,
                           args.model_size, args.instruct)
    print(f"✓ Saved to {result}")

if __name__ == "__main__":
    main()
