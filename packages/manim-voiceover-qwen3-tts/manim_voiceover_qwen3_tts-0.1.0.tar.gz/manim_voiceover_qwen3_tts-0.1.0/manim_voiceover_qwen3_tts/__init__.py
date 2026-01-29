"""Qwen3-TTS integration for manim-voiceover.

This package provides three speech services for manim-voiceover:

- Qwen3PresetVoiceService: Use Qwen3's built-in premium voices (easiest)
- Qwen3VoiceDesignService: Create voices from natural language descriptions
- Qwen3VoiceCloningService: Clone voices from reference audio samples

Example usage:

    from manim import *
    from manim_voiceover import VoiceoverScene
    from manim_voiceover_qwen3_tts import Qwen3PresetVoiceService

    class MyScene(VoiceoverScene):
        def construct(self):
            self.set_speech_service(
                Qwen3PresetVoiceService(
                    speaker="Ryan",
                    language="English",
                )
            )

            with self.voiceover(text="Hello, world!") as tracker:
                self.play(Create(Circle()), run_time=tracker.duration)
"""

from manim_voiceover_qwen3_tts.services.qwen3 import (
    Qwen3VoiceCloningService,
    Qwen3VoiceDesignService,
    Qwen3PresetVoiceService,
    VoiceProfile,
)

__version__ = "0.1.0"

__all__ = [
    "Qwen3VoiceCloningService",
    "Qwen3VoiceDesignService",
    "Qwen3PresetVoiceService",
    "VoiceProfile",
]
