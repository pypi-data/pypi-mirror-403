"""Example: Emotion Control with Preset Voices.

Shows how to control emotions and speaking styles using the `instruct`
parameter. Preset voices support style instructions like "speak happily"
or "speak with sadness".

Uses: Qwen3PresetVoiceService (with instruct parameter)

Run with:
    manim -pql emotion_showcase.py EmotionShowcase
"""

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover_qwen3_tts import Qwen3PresetVoiceService


class EmotionShowcase(VoiceoverScene):
    """Showcase different emotions using the instruct parameter."""

    def construct(self):
        # Base service - we'll override instruct per voiceover
        self.set_speech_service(
            Qwen3PresetVoiceService(
                speaker="Ryan",
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        # Title
        title = Text("Emotion Showcase", font_size=48, color=BLUE)
        subtitle = Text("Same voice, different emotions", font_size=28, color=GRAY)
        subtitle.next_to(title, DOWN)

        self.play(Write(title), FadeIn(subtitle))
        self.wait(0.5)

        with self.voiceover(
            text="Watch how the same voice can express completely different emotions.",
        ) as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(title), FadeOut(subtitle))

        # Define emotions to showcase
        emotions = [
            {
                "name": "Happy",
                "color": YELLOW,
                "instruct": "Very happy and cheerful, with a bright upbeat tone",
                "text": "This is absolutely wonderful! I'm so excited to share this with you!",
            },
            {
                "name": "Sad",
                "color": BLUE,
                "instruct": "Speak with sadness and melancholy, slower and softer",
                "text": "I'm sorry to tell you this... it's been a difficult time for everyone.",
            },
            {
                "name": "Angry",
                "color": RED,
                "instruct": "Speak in a particularly angry and frustrated tone",
                "text": "This is completely unacceptable! How could this happen again?",
            },
            {
                "name": "Excited",
                "color": ORANGE,
                "instruct": "Extremely excited and energetic, speaking faster with enthusiasm",
                "text": "Oh my gosh, you won't believe what just happened! This is amazing!",
            },
            {
                "name": "Calm",
                "color": GREEN,
                "instruct": "Speak in a calm, soothing, and relaxed manner",
                "text": "Take a deep breath. Everything is going to be just fine.",
            },
            {
                "name": "Nervous",
                "color": PURPLE,
                "instruct": "Speak with nervousness and uncertainty, hesitant",
                "text": "Um, well, I'm not really sure about this... maybe we should reconsider?",
            },
            {
                "name": "Confident",
                "color": GOLD,
                "instruct": "Speak with strong authority and unwavering confidence",
                "text": "I know exactly what we need to do. Follow my lead and we'll succeed.",
            },
            {
                "name": "Whisper",
                "color": GRAY,
                "instruct": "Speak in a soft, secretive whisper",
                "text": "Come closer... I have something important to tell you... it's a secret.",
            },
        ]

        for i, emotion in enumerate(emotions):
            # Create emotion label
            label = Text(emotion["name"], font_size=56, color=emotion["color"])
            label.to_edge(UP, buff=1)

            # Create instruction display
            instruct_label = Text("Instruction:", font_size=20, color=GRAY)
            instruct_text = Text(
                f'"{emotion["instruct"][:50]}..."' if len(emotion["instruct"]) > 50
                else f'"{emotion["instruct"]}"',
                font_size=18,
                color=WHITE,
            )
            instruct_group = VGroup(instruct_label, instruct_text).arrange(DOWN, buff=0.1)
            instruct_group.to_edge(DOWN, buff=1)

            # Animate
            self.play(FadeIn(label), FadeIn(instruct_group))

            with self.voiceover(
                text=emotion["text"],
                instruct=emotion["instruct"],
            ) as tracker:
                # Pulse the label during speech
                self.play(
                    label.animate.scale(1.1),
                    rate_func=there_and_back,
                    run_time=tracker.duration,
                )

            self.wait(0.3)
            self.play(FadeOut(label), FadeOut(instruct_group))

        # Closing
        closing = Text("The power of emotional expression!", font_size=36, color=BLUE)
        self.play(Write(closing))

        with self.voiceover(
            text="And that's how you can bring your animations to life with emotional voiceovers!",
            instruct="Speak with warmth and satisfaction",
        ) as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(closing))
        self.wait(0.5)
