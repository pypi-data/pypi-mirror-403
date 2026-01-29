"""Example: Voice Design Service.

Same mathematical content delivered with different designed voices.
Each voice is created from a natural language description - no
reference audio needed.

Uses: Qwen3VoiceDesignService

Run with:
    manim -pql voice_design.py VoiceDesignDemo
"""

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover_qwen3_tts import Qwen3VoiceDesignService


# The same content delivered with different designed voices
CONTENT = {
    "intro": "Today we're going to learn about the Pythagorean theorem.",
    "explanation": "In a right triangle, the square of the hypotenuse equals the sum of the squares of the other two sides.",
    "formula": "A squared plus B squared equals C squared.",
    "conclusion": "This fundamental theorem has countless applications in mathematics and science.",
}

# Different voice designs - each created from a text description
VOICES = [
    {
        "name": "Documentary Narrator",
        "color": GREEN,
        "voice_description": (
            "A deep, authoritative male voice with gravitas, like a nature "
            "documentary narrator. Measured pace with dramatic pauses."
        ),
    },
    {
        "name": "Friendly Teacher",
        "color": BLUE,
        "voice_description": (
            "A warm, friendly female voice with clear enunciation. Patient and "
            "encouraging, like a favorite teacher explaining concepts to students."
        ),
    },
    {
        "name": "Corporate Presenter",
        "color": GRAY,
        "voice_description": (
            "A professional, polished business voice. Clear enunciation, "
            "confident tone, perfect for boardroom presentations."
        ),
    },
    {
        "name": "Dramatic Actor",
        "color": PURPLE,
        "voice_description": (
            "A theatrical, dramatic voice with expressive intonation. "
            "Emphasizes key words with passion, like a stage actor."
        ),
    },
]


class VoiceDesignDemo(VoiceoverScene):
    """Demonstrate voice design with different voice descriptions."""

    def construct(self):
        # Title
        title = Text("Voice Design", font_size=48, color=BLUE)
        subtitle = Text("Create any voice from a description", font_size=28, color=GRAY)
        subtitle.next_to(title, DOWN)

        self.play(Write(title), FadeIn(subtitle))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Create the triangle
        triangle = Polygon(
            ORIGIN, RIGHT * 3, RIGHT * 3 + UP * 2,
            color=WHITE,
            fill_opacity=0.2,
        )
        triangle.move_to(ORIGIN)

        # Labels
        a_label = Text("a", font_size=24).next_to(triangle, DOWN, buff=0.1)
        b_label = Text("b", font_size=24).next_to(triangle, RIGHT, buff=0.1)
        c_label = Text("c", font_size=24)
        c_label.move_to(triangle.get_center() + UL * 0.5)

        # Right angle marker
        right_angle = Square(side_length=0.3, color=WHITE)
        right_angle.move_to(triangle.get_vertices()[1] + UL * 0.15)

        triangle_group = VGroup(triangle, a_label, b_label, c_label, right_angle)
        triangle_group.scale(0.8).shift(DOWN * 0.5)

        # Formula
        formula = MathTex("a^2 + b^2 = c^2", font_size=48)
        formula.to_edge(DOWN, buff=1)

        for voice in VOICES:
            # Set up voice design service
            self.set_speech_service(
                Qwen3VoiceDesignService(
                    voice_description=voice["voice_description"],
                    language="English",
                    device="cuda:0",
                    use_flash_attention=False,
                )
            )

            # Voice name header
            voice_name = Text(voice["name"], font_size=36, color=voice["color"])
            voice_name.to_edge(UP, buff=0.5)

            # Show truncated description
            desc_preview = Text(
                f'"{voice["voice_description"][:50]}..."',
                font_size=16,
                color=GRAY,
            )
            desc_preview.next_to(voice_name, DOWN, buff=0.2)

            self.play(FadeIn(voice_name), FadeIn(desc_preview))

            # Intro
            with self.voiceover(text=CONTENT["intro"]) as tracker:
                self.play(Create(triangle_group), run_time=tracker.duration)

            # Explanation
            with self.voiceover(text=CONTENT["explanation"]) as tracker:
                self.play(
                    Indicate(a_label, color=voice["color"]),
                    run_time=tracker.duration / 3,
                )
                self.play(
                    Indicate(b_label, color=voice["color"]),
                    run_time=tracker.duration / 3,
                )
                self.play(
                    Indicate(c_label, color=voice["color"]),
                    run_time=tracker.duration / 3,
                )

            # Formula
            with self.voiceover(text=CONTENT["formula"]) as tracker:
                self.play(Write(formula), run_time=tracker.duration)

            # Conclusion
            with self.voiceover(text=CONTENT["conclusion"]) as tracker:
                self.play(
                    triangle_group.animate.set_color(voice["color"]),
                    formula.animate.set_color(voice["color"]),
                    run_time=tracker.duration,
                )

            self.wait(0.5)

            # Clear for next voice
            self.play(
                FadeOut(voice_name),
                FadeOut(desc_preview),
                FadeOut(triangle_group),
                FadeOut(formula),
            )

            # Recreate for next iteration
            triangle = Polygon(
                ORIGIN, RIGHT * 3, RIGHT * 3 + UP * 2,
                color=WHITE,
                fill_opacity=0.2,
            )
            triangle.move_to(ORIGIN)
            a_label = Text("a", font_size=24).next_to(triangle, DOWN, buff=0.1)
            b_label = Text("b", font_size=24).next_to(triangle, RIGHT, buff=0.1)
            c_label = Text("c", font_size=24)
            c_label.move_to(triangle.get_center() + UL * 0.5)
            right_angle = Square(side_length=0.3, color=WHITE)
            right_angle.move_to(triangle.get_vertices()[1] + UL * 0.15)
            triangle_group = VGroup(triangle, a_label, b_label, c_label, right_angle)
            triangle_group.scale(0.8).shift(DOWN * 0.5)
            formula = MathTex("a^2 + b^2 = c^2", font_size=48)
            formula.to_edge(DOWN, buff=1)

        # Final summary
        summary = VGroup(
            Text("4 Unique Voices", font_size=32, color=WHITE),
            Text("Created from text descriptions", font_size=28, color=BLUE),
        ).arrange(DOWN, buff=0.3)

        self.play(FadeIn(summary))
        self.wait(2)
        self.play(FadeOut(summary))
