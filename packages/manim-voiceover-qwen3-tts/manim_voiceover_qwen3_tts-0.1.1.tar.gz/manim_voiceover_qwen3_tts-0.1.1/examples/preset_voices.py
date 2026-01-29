"""Example: Preset Voices and Multilingual Support.

Demonstrates Qwen3's built-in preset voices across different languages.
Shows how to switch between speakers and languages.

Uses: Qwen3PresetVoiceService

Run with:
    manim -pql preset_voices.py PresetVoicesDemo
"""

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover_qwen3_tts import Qwen3PresetVoiceService


# Available preset speakers by language
SPEAKERS = [
    {"speaker": "Ryan", "language": "English", "text": "Hello! I'm Ryan, an English speaker."},
    {"speaker": "Aiden", "language": "English", "text": "And I'm Aiden, another English voice."},
    {"speaker": "Vivian", "language": "Chinese", "text": "你好！我是Vivian，中文语音。"},
    {"speaker": "Ono_Anna", "language": "Japanese", "text": "こんにちは！私はOno Annaです。"},
    {"speaker": "Sohee", "language": "Korean", "text": "안녕하세요! 저는 Sohee입니다."},
]


class PresetVoicesDemo(VoiceoverScene):
    """Showcase preset voices across multiple languages."""

    def construct(self):
        # Title
        title = Text("Preset Voices", font_size=48, color=BLUE)
        subtitle = Text("Built-in speakers across 10 languages", font_size=28, color=GRAY)
        subtitle.next_to(title, DOWN)

        self.play(Write(title), FadeIn(subtitle))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Show each preset speaker
        for preset in SPEAKERS:
            # Set up voice service for this speaker
            self.set_speech_service(
                Qwen3PresetVoiceService(
                    speaker=preset["speaker"],
                    language=preset["language"],
                    device="cuda:0",
                    use_flash_attention=False,
                )
            )

            # Display speaker info
            speaker_name = Text(preset["speaker"], font_size=48, color=BLUE)
            speaker_name.to_edge(UP, buff=1)

            language_label = Text(preset["language"], font_size=28, color=GRAY)
            language_label.next_to(speaker_name, DOWN, buff=0.3)

            self.play(FadeIn(speaker_name), FadeIn(language_label))

            # Speak the introduction
            with self.voiceover(text=preset["text"]) as tracker:
                self.play(
                    Indicate(speaker_name, color=WHITE),
                    run_time=tracker.duration,
                )

            self.wait(0.3)
            self.play(FadeOut(speaker_name), FadeOut(language_label))

        # Summary
        summary = VGroup(
            Text("9 Preset Speakers", font_size=36),
            Text("10 Languages Supported", font_size=28, color=GRAY),
        ).arrange(DOWN, buff=0.3)

        self.play(FadeIn(summary))

        # Use Ryan for closing
        self.set_speech_service(
            Qwen3PresetVoiceService(
                speaker="Ryan",
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="Preset voices are the easiest way to get started. No setup required!"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(1)
        self.play(FadeOut(summary))
