"""Example: Voice Cloning Service.

Clone any voice from a short audio sample (3+ seconds). The model learns
the voice characteristics and can generate new speech in that voice.

Uses: Qwen3VoiceCloningService

This example includes a sample narrator voice in voices/narrator.wav.
To add your own voices, create a VoiceProfile with:
    - ref_audio: path to your .wav file (3+ seconds of clear speech)
    - ref_text: exact transcript of what's spoken in the audio

Run with:
    manim -pql voice_cloning.py VoiceCloningDemo
"""

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover_qwen3_tts import Qwen3VoiceCloningService, VoiceProfile


# Define voice profile for the narrator
# The ref_text must exactly match what's said in the audio file
narrator_voice = VoiceProfile(
    name="narrator",
    ref_audio="/voices/narrator.wav",
    ref_text=(
        "The golden sun dipped below the horizon, casting long, dramatic shadows "
        "across the quiet valley. Technology often bridges the gap between our "
        "wildest dreams and reality, yet it requires a delicate touch to master."
    ),
    language="English",
)


class VoiceCloningDemo(VoiceoverScene):
    """Demo of Qwen3 voice cloning."""

    def construct(self):
        # Initialize with the narrator voice profile
        self.set_speech_service(
            Qwen3VoiceCloningService(
                voices=[narrator_voice],
                default_voice="narrator",
                use_flash_attention=False,
            )
        )

        # Title
        title = Text("Voice Cloning Demo", font_size=48, color=BLUE)

        with self.voiceover(
            text="Welcome to the voice cloning demonstration. "
            "My voice was cloned from just a few seconds of audio."
        ) as tracker:
            self.play(Write(title), run_time=tracker.duration)

        self.wait(0.5)
        self.play(title.animate.to_edge(UP))

        # Show the concept
        concept = VGroup(
            Text("Reference Audio", font_size=28, color=YELLOW),
            Text("+", font_size=28),
            Text("Transcript", font_size=28, color=GREEN),
            Text("=", font_size=28),
            Text("Cloned Voice", font_size=28, color=BLUE),
        ).arrange(RIGHT, buff=0.3)

        with self.voiceover(
            text="Voice cloning works by analyzing a short audio sample "
            "along with its transcript to learn the voice characteristics."
        ) as tracker:
            self.play(FadeIn(concept), run_time=tracker.duration)

        self.wait(0.5)

        # Show code example (using Text since Code API varies between manim versions)
        code_text = '''VoiceProfile(
    name="narrator",
    ref_audio="voices/narrator.wav",
    ref_text="The exact transcript...",
)'''
        code = Text(code_text, font="Monospace", font_size=24)
        code.shift(DOWN * 0.5)

        with self.voiceover(
            text="Setting up voice cloning is straightforward. "
            "Define a voice profile with the audio path and transcript, "
            "then pass it to the cloning service."
        ) as tracker:
            self.play(
                concept.animate.scale(0.7).to_edge(UP, buff=1.5),
                FadeOut(title),
                FadeIn(code),
                run_time=tracker.duration,
            )

        self.wait(0.5)

        # Demonstrate the cloned voice
        with self.voiceover(
            text="Once configured, the cloned voice can say anything you want. "
            "The model captures the tone, pace, and characteristics of the original speaker."
        ) as tracker:
            self.play(
                Indicate(code, color=YELLOW),
                run_time=tracker.duration,
            )

        self.wait(0.5)

        # Closing
        with self.voiceover(
            text="This is perfect for creating consistent narration "
            "or bringing specific voices to your animations."
        ) as tracker:
            self.play(
                FadeOut(code),
                FadeOut(concept),
                run_time=tracker.duration,
            )

        # Final message
        closing = Text("Clone any voice with just 3 seconds of audio!",
                       font_size=32, color=BLUE)

        self.play(FadeIn(closing))
        self.wait(2)
        self.play(FadeOut(closing))
