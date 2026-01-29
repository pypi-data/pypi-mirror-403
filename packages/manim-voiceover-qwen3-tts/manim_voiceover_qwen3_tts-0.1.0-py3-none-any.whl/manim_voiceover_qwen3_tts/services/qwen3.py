"""Qwen3-TTS speech services for manim-voiceover."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from manim import logger

from manim_voiceover.helper import remove_bookmarks, wav2mp3
from manim_voiceover.services.base import SpeechService


@dataclass
class VoiceProfile:
    """A voice profile for voice cloning.

    Stores reference audio and transcript for a named voice/character.
    Use this to define consistent voices for different characters in your animation.

    Attributes:
        name: Identifier for this voice (e.g., "narrator", "character1")
        ref_audio: Path to reference audio file (3+ seconds recommended)
        ref_text: Transcript of the reference audio
        language: Language code (default: "Auto" for auto-detection)
    """
    name: str
    ref_audio: str
    ref_text: str
    language: str = "Auto"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        """Create from dictionary."""
        return cls(**data)


class Qwen3VoiceCloningService(SpeechService):
    """Voice cloning service using Qwen3-TTS Base model.

    Use this service when you have reference audio samples and want to clone
    voices for your animation characters. Requires 3+ seconds of reference audio.

    Example:
        ```python
        from manim_voiceover_qwen3_tts import Qwen3VoiceCloningService, VoiceProfile

        # Define voice profiles for your characters
        narrator = VoiceProfile(
            name="narrator",
            ref_audio="voices/narrator_sample.wav",
            ref_text="This is a sample of the narrator's voice.",
        )

        class MyScene(VoiceoverScene):
            def construct(self):
                service = Qwen3VoiceCloningService(
                    voices=[narrator],
                    default_voice="narrator",
                )
                self.set_speech_service(service)

                with self.voiceover(text="Hello world!") as tracker:
                    self.play(Create(circle), run_time=tracker.duration)
        ```
    """

    def __init__(
        self,
        model: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        voices: Optional[List[VoiceProfile]] = None,
        default_voice: Optional[str] = None,
        device: str = "cuda:0",
        dtype: str = "bfloat16",
        use_flash_attention: bool = True,
        output_format: str = "mp3",
        **kwargs,
    ):
        """Initialize the Qwen3-TTS voice cloning service.

        Args:
            model: HuggingFace model ID for the Base model.
            voices: List of VoiceProfile objects defining available voices.
            default_voice: Name of the default voice to use.
            device: Device to run the model on (e.g., "cuda:0", "cpu").
            dtype: Data type for model weights ("bfloat16", "float16", "float32").
            use_flash_attention: Whether to use FlashAttention 2 if available.
            output_format: Output audio format ("mp3" or "wav").
            **kwargs: Additional arguments passed to SpeechService.
        """
        self.model_id = model
        self.voices: Dict[str, VoiceProfile] = {}
        self.default_voice = default_voice
        self.device = device
        self.dtype = dtype
        self.use_flash_attention = use_flash_attention
        self.output_format = output_format

        # Register voice profiles
        if voices:
            for voice in voices:
                self.voices[voice.name] = voice
            if default_voice is None and len(voices) > 0:
                self.default_voice = voices[0].name

        # Lazy-loaded model
        self._model = None
        self._voice_prompts: Dict[str, Any] = {}

        SpeechService.__init__(self, **kwargs)

    def _get_model(self):
        """Lazy-load the TTS model."""
        if self._model is None:
            try:
                import torch
                from qwen_tts import Qwen3TTSModel
            except ImportError:
                raise ImportError(
                    "qwen-tts is not installed. Install it with: pip install qwen-tts"
                )

            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32,
            }

            attn_impl = "flash_attention_2" if self.use_flash_attention else "sdpa"

            logger.info(f"Loading Qwen3-TTS model: {self.model_id}")
            self._model = Qwen3TTSModel.from_pretrained(
                self.model_id,
                device_map=self.device,
                dtype=dtype_map.get(self.dtype, torch.bfloat16),
                attn_implementation=attn_impl,
            )
        return self._model

    def _get_voice_prompt(self, voice_name: str):
        """Get or create a cached voice prompt for efficient generation."""
        if voice_name not in self._voice_prompts:
            if voice_name not in self.voices:
                raise ValueError(
                    f"Voice '{voice_name}' not found. "
                    f"Available voices: {list(self.voices.keys())}"
                )

            voice = self.voices[voice_name]
            model = self._get_model()

            logger.info(f"Creating voice prompt for: {voice_name}")
            self._voice_prompts[voice_name] = model.create_voice_clone_prompt(
                ref_audio=voice.ref_audio,
                ref_text=voice.ref_text,
            )

        return self._voice_prompts[voice_name]

    def add_voice(self, voice: VoiceProfile) -> None:
        """Add a voice profile at runtime.

        Args:
            voice: VoiceProfile to add.
        """
        self.voices[voice.name] = voice
        # Clear cached prompt if it exists
        if voice.name in self._voice_prompts:
            del self._voice_prompts[voice.name]

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[str] = None,
        path: Optional[str] = None,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Generate speech from text using voice cloning.

        Args:
            text: Text to synthesize (may contain bookmarks).
            cache_dir: Directory for caching audio files.
            path: Optional specific output path.
            voice: Voice profile name to use (defaults to default_voice).
            language: Language override (defaults to voice profile setting).
            **kwargs: Additional generation parameters.

        Returns:
            Dictionary with audio file information for manim-voiceover.
        """
        import soundfile as sf

        if cache_dir is None:
            cache_dir = self.cache_dir

        # Resolve voice
        voice_name = voice or self.default_voice
        if voice_name is None:
            raise ValueError(
                "No voice specified and no default_voice set. "
                "Either pass voice= or set default_voice in constructor."
            )

        voice_profile = self.voices.get(voice_name)
        if voice_profile is None:
            raise ValueError(
                f"Voice '{voice_name}' not found. "
                f"Available: {list(self.voices.keys())}"
            )

        # Clean text for synthesis
        input_text = remove_bookmarks(text)
        lang = language or voice_profile.language

        # Build input data for caching
        input_data = {
            "input_text": input_text,
            "service": "qwen3_tts_clone",
            "config": {
                "model": self.model_id,
                "voice": voice_name,
                "ref_audio": voice_profile.ref_audio,
                "ref_text": voice_profile.ref_text,
                "language": lang,
            },
        }

        # Check cache
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached

        # Generate filename
        if path is None:
            audio_path = self.get_audio_basename(input_data) + f".{self.output_format}"
        else:
            audio_path = path

        output_path = Path(cache_dir) / audio_path

        # Generate audio
        model = self._get_model()
        voice_prompt = self._get_voice_prompt(voice_name)

        logger.info(f"Generating speech for: {input_text[:50]}...")
        wavs, sr = model.generate_voice_clone(
            text=input_text,
            language=lang,
            voice_clone_prompt=voice_prompt,
        )

        # Save audio
        wav_path = output_path.with_suffix(".wav")
        sf.write(str(wav_path), wavs[0], sr)

        if self.output_format == "mp3":
            wav2mp3(str(wav_path), str(output_path))
        else:
            output_path = wav_path
            audio_path = audio_path.replace(".mp3", ".wav")

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }


class Qwen3VoiceDesignService(SpeechService):
    """Voice design service using natural language descriptions.

    Create custom voices by describing them in natural language, without
    needing reference audio samples.

    Example:
        ```python
        from manim_voiceover_qwen3_tts import Qwen3VoiceDesignService

        class MyScene(VoiceoverScene):
            def construct(self):
                service = Qwen3VoiceDesignService(
                    voice_description="A warm, friendly female voice with "
                                      "a slight British accent, speaking clearly "
                                      "and professionally.",
                    language="English",
                )
                self.set_speech_service(service)

                with self.voiceover(text="Welcome to our tutorial!") as tracker:
                    self.play(FadeIn(title), run_time=tracker.duration)
        ```
    """

    def __init__(
        self,
        voice_description: str,
        model: str = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        language: str = "English",
        device: str = "cuda:0",
        dtype: str = "bfloat16",
        use_flash_attention: bool = True,
        output_format: str = "mp3",
        **kwargs,
    ):
        """Initialize the voice design service.

        Args:
            voice_description: Natural language description of the desired voice.
            model: HuggingFace model ID for the VoiceDesign model.
            language: Default language for synthesis.
            device: Device to run the model on.
            dtype: Data type for model weights.
            use_flash_attention: Whether to use FlashAttention 2.
            output_format: Output audio format ("mp3" or "wav").
            **kwargs: Additional arguments passed to SpeechService.
        """
        self.voice_description = voice_description
        self.model_id = model
        self.language = language
        self.device = device
        self.dtype = dtype
        self.use_flash_attention = use_flash_attention
        self.output_format = output_format

        self._model = None

        SpeechService.__init__(self, **kwargs)

    def _get_model(self):
        """Lazy-load the TTS model."""
        if self._model is None:
            try:
                import torch
                from qwen_tts import Qwen3TTSModel
            except ImportError:
                raise ImportError(
                    "qwen-tts is not installed. Install it with: pip install qwen-tts"
                )

            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32,
            }

            attn_impl = "flash_attention_2" if self.use_flash_attention else "sdpa"

            logger.info(f"Loading Qwen3-TTS model: {self.model_id}")
            self._model = Qwen3TTSModel.from_pretrained(
                self.model_id,
                device_map=self.device,
                dtype=dtype_map.get(self.dtype, torch.bfloat16),
                attn_implementation=attn_impl,
            )
        return self._model

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[str] = None,
        path: Optional[str] = None,
        voice_description: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Generate speech using voice design.

        Args:
            text: Text to synthesize.
            cache_dir: Directory for caching audio files.
            path: Optional specific output path.
            voice_description: Override the default voice description.
            language: Language override.
            **kwargs: Additional generation parameters.

        Returns:
            Dictionary with audio file information.
        """
        import soundfile as sf

        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        desc = voice_description or self.voice_description
        lang = language or self.language

        input_data = {
            "input_text": input_text,
            "service": "qwen3_tts_design",
            "config": {
                "model": self.model_id,
                "voice_description": desc,
                "language": lang,
            },
        }

        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached

        if path is None:
            audio_path = self.get_audio_basename(input_data) + f".{self.output_format}"
        else:
            audio_path = path

        output_path = Path(cache_dir) / audio_path

        model = self._get_model()

        logger.info(f"Generating speech with voice design: {input_text[:50]}...")
        wavs, sr = model.generate_voice_design(
            text=input_text,
            language=lang,
            instruct=desc,
        )

        wav_path = output_path.with_suffix(".wav")
        sf.write(str(wav_path), wavs[0], sr)

        if self.output_format == "mp3":
            wav2mp3(str(wav_path), str(output_path))
        else:
            output_path = wav_path
            audio_path = audio_path.replace(".mp3", ".wav")

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }


class Qwen3PresetVoiceService(SpeechService):
    """Preset voice service using Qwen3's built-in premium voices.

    Use this service for high-quality preset voices without needing
    reference audio or voice descriptions. Supports emotion/style control
    via the instruct parameter.

    Available speakers:
        - Chinese: Vivian, Serena, Uncle_Fu, Dylan, Eric
        - English: Ryan, Aiden
        - Japanese: Ono_Anna
        - Korean: Sohee

    Example:
        ```python
        from manim_voiceover_qwen3_tts import Qwen3PresetVoiceService

        class MyScene(VoiceoverScene):
            def construct(self):
                service = Qwen3PresetVoiceService(
                    speaker="Ryan",
                    language="English",
                    instruct="Speak with enthusiasm and energy",
                )
                self.set_speech_service(service)

                with self.voiceover(text="Let's learn something new!") as tracker:
                    self.play(Create(diagram), run_time=tracker.duration)
        ```
    """

    AVAILABLE_SPEAKERS = [
        "Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric",  # Chinese
        "Ryan", "Aiden",  # English
        "Ono_Anna",  # Japanese
        "Sohee",  # Korean
    ]

    def __init__(
        self,
        speaker: str = "Ryan",
        model: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        language: str = "English",
        instruct: Optional[str] = None,
        device: str = "cuda:0",
        dtype: str = "bfloat16",
        use_flash_attention: bool = True,
        output_format: str = "mp3",
        **kwargs,
    ):
        """Initialize the custom voice service.

        Args:
            speaker: Name of the preset speaker to use.
            model: HuggingFace model ID for the CustomVoice model.
            language: Default language for synthesis.
            instruct: Optional instruction for emotion/style control.
            device: Device to run the model on.
            dtype: Data type for model weights.
            use_flash_attention: Whether to use FlashAttention 2.
            output_format: Output audio format ("mp3" or "wav").
            **kwargs: Additional arguments passed to SpeechService.
        """
        if speaker not in self.AVAILABLE_SPEAKERS:
            logger.warning(
                f"Speaker '{speaker}' not in known speakers: {self.AVAILABLE_SPEAKERS}. "
                "Proceeding anyway in case of new speakers."
            )

        self.speaker = speaker
        self.model_id = model
        self.language = language
        self.instruct = instruct
        self.device = device
        self.dtype = dtype
        self.use_flash_attention = use_flash_attention
        self.output_format = output_format

        self._model = None

        SpeechService.__init__(self, **kwargs)

    def _get_model(self):
        """Lazy-load the TTS model."""
        if self._model is None:
            try:
                import torch
                from qwen_tts import Qwen3TTSModel
            except ImportError:
                raise ImportError(
                    "qwen-tts is not installed. Install it with: pip install qwen-tts"
                )

            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32,
            }

            attn_impl = "flash_attention_2" if self.use_flash_attention else "sdpa"

            logger.info(f"Loading Qwen3-TTS model: {self.model_id}")
            self._model = Qwen3TTSModel.from_pretrained(
                self.model_id,
                device_map=self.device,
                dtype=dtype_map.get(self.dtype, torch.bfloat16),
                attn_implementation=attn_impl,
            )
        return self._model

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[str] = None,
        path: Optional[str] = None,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        instruct: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Generate speech using a custom voice.

        Args:
            text: Text to synthesize.
            cache_dir: Directory for caching audio files.
            path: Optional specific output path.
            speaker: Override the default speaker.
            language: Language override.
            instruct: Override the default instruction.
            **kwargs: Additional generation parameters.

        Returns:
            Dictionary with audio file information.
        """
        import soundfile as sf

        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        spk = speaker or self.speaker
        lang = language or self.language
        inst = instruct if instruct is not None else self.instruct

        input_data = {
            "input_text": input_text,
            "service": "qwen3_tts_custom",
            "config": {
                "model": self.model_id,
                "speaker": spk,
                "language": lang,
                "instruct": inst,
            },
        }

        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached

        if path is None:
            audio_path = self.get_audio_basename(input_data) + f".{self.output_format}"
        else:
            audio_path = path

        output_path = Path(cache_dir) / audio_path

        model = self._get_model()

        logger.info(f"Generating speech with {spk}: {input_text[:50]}...")

        gen_kwargs = {
            "text": input_text,
            "language": lang,
            "speaker": spk,
        }
        if inst:
            gen_kwargs["instruct"] = inst

        wavs, sr = model.generate_custom_voice(**gen_kwargs)

        wav_path = output_path.with_suffix(".wav")
        sf.write(str(wav_path), wavs[0], sr)

        if self.output_format == "mp3":
            wav2mp3(str(wav_path), str(output_path))
        else:
            output_path = wav_path
            audio_path = audio_path.replace(".mp3", ".wav")

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }
