"""Example: Multi-Character Storytelling.

A short animated story with narrator, hero, mentor, and villain - each
with a distinct voice created from natural language descriptions.
Demonstrates switching between voice designs mid-scene.

Uses: Qwen3VoiceDesignService (switching voice_description per character)

Run with:
    manim -pql storytelling_scene.py StorytellingScene
"""

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover_qwen3_tts import Qwen3VoiceDesignService


class StorytellingScene(VoiceoverScene):
    """A short animated story with multiple character voices."""

    def construct(self):
        # Character voice descriptions
        narrator_voice = (
            "A warm, mature male voice with a storytelling quality. "
            "Speaks with gravitas and gentle pacing, drawing the listener in."
        )

        hero_voice = (
            "A young, brave male voice full of determination and courage. "
            "Confident but not arrogant, with youthful energy."
        )

        mentor_voice = (
            "An elderly, wise female voice with warmth and patience. "
            "Speaks slowly with deep wisdom, like a caring grandmother."
        )

        villain_voice = (
            "A deep, menacing male voice with a sinister edge. "
            "Speaks with cold calculation and subtle threat."
        )

        # Title card
        title = Text("The Quest for Knowledge", font_size=48, color=GOLD)
        subtitle = Text("A Manim Story", font_size=28, color=GRAY)
        subtitle.next_to(title, DOWN)

        self.play(Write(title), FadeIn(subtitle))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Scene setup
        ground = Line(LEFT * 7, RIGHT * 7, color=GREEN_E).shift(DOWN * 2)
        self.add(ground)

        # Characters as simple shapes
        hero = VGroup(
            Circle(radius=0.3, color=BLUE, fill_opacity=1),  # Head
            Triangle(color=BLUE, fill_opacity=1).scale(0.4).shift(DOWN * 0.5),  # Body
        )
        hero.shift(LEFT * 4 + DOWN * 1)

        mentor = VGroup(
            Circle(radius=0.35, color=PURPLE, fill_opacity=1),
            Triangle(color=PURPLE, fill_opacity=1).scale(0.5).shift(DOWN * 0.55),
        )
        mentor.shift(DOWN * 1)

        villain = VGroup(
            Circle(radius=0.4, color=RED, fill_opacity=1),
            Triangle(color=RED, fill_opacity=1).scale(0.5).shift(DOWN * 0.6),
        )
        villain.shift(RIGHT * 4 + DOWN * 0.9)

        # Character labels
        hero_label = Text("Hero", font_size=16, color=BLUE).next_to(hero, UP)
        mentor_label = Text("Mentor", font_size=16, color=PURPLE).next_to(mentor, UP)
        villain_label = Text("Villain", font_size=16, color=RED).next_to(villain, UP)

        # ========== ACT 1: Introduction ==========

        # Narrator introduction
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=narrator_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="In a world where knowledge was power, a young hero embarked on a quest."
        ) as tracker:
            self.play(
                FadeIn(hero),
                FadeIn(hero_label),
                run_time=tracker.duration,
            )

        # Hero speaks
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=hero_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="I must find the ancient theorem! It's the only way to save our village."
        ) as tracker:
            self.play(
                hero.animate.shift(RIGHT * 1),
                hero_label.animate.shift(RIGHT * 1),
                run_time=tracker.duration,
            )

        # ========== ACT 2: Meeting the Mentor ==========

        # Narrator
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=narrator_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="On his journey, he met a wise mentor who knew the secrets of mathematics."
        ) as tracker:
            self.play(
                FadeIn(mentor),
                FadeIn(mentor_label),
                run_time=tracker.duration,
            )

        # Mentor speaks
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=mentor_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="Young one, the theorem you seek lies within the Circle of Truth. But beware... you are not alone in your quest."
        ) as tracker:
            self.play(
                Indicate(mentor, color=WHITE),
                run_time=tracker.duration,
            )

        # ========== ACT 3: The Villain Appears ==========

        # Narrator
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=narrator_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="From the shadows emerged a dark figure, the villain who sought the same power."
        ) as tracker:
            self.play(
                FadeIn(villain),
                FadeIn(villain_label),
                run_time=tracker.duration,
            )

        # Villain speaks
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=villain_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="The theorem will be mine. And with it, I shall control all knowledge in the realm."
        ) as tracker:
            self.play(
                villain.animate.scale(1.2),
                run_time=tracker.duration,
            )

        # ========== ACT 4: Resolution ==========

        # Hero responds
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=hero_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="Knowledge belongs to everyone! I won't let you take it!"
        ) as tracker:
            self.play(
                hero.animate.shift(RIGHT * 2),
                hero_label.animate.shift(RIGHT * 2),
                run_time=tracker.duration,
            )

        # Create the "theorem" - a glowing circle
        theorem = Circle(radius=0.8, color=GOLD, fill_opacity=0.3)
        theorem.shift(UP * 1)
        theorem_label = Text("πr²", font_size=32, color=GOLD)
        theorem_label.move_to(theorem)

        # Narrator conclusion
        self.set_speech_service(
            Qwen3VoiceDesignService(
                voice_description=narrator_voice,
                language="English",
                device="cuda:0",
                use_flash_attention=False,
            )
        )

        with self.voiceover(
            text="And so, the hero discovered that the true theorem was not a weapon, but a gift to be shared with all."
        ) as tracker:
            self.play(
                Create(theorem),
                Write(theorem_label),
                villain.animate.scale(0.8).shift(RIGHT * 2),
                run_time=tracker.duration,
            )

        self.wait(0.5)

        with self.voiceover(
            text="The end."
        ) as tracker:
            self.play(
                FadeOut(hero), FadeOut(hero_label),
                FadeOut(mentor), FadeOut(mentor_label),
                FadeOut(villain), FadeOut(villain_label),
                theorem.animate.scale(2),
                theorem_label.animate.scale(1.5),
                run_time=tracker.duration,
            )

        self.wait(1)

        # Credits
        credits = VGroup(
            Text("Created with", font_size=24, color=GRAY),
            Text("manim-qwen3-tts", font_size=32, color=BLUE),
        ).arrange(DOWN)

        self.play(
            FadeOut(theorem),
            FadeOut(theorem_label),
            FadeOut(ground),
            FadeIn(credits),
        )
        self.wait(2)
        self.play(FadeOut(credits))
