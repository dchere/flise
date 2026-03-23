from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import random


CRITIC_SYSTEM_PROMPT = (
    "You are an art critic for the Flise vectorization project. "
    "Compare the [User Intent] with the [Generated Image]. "
    "Check for: Color accuracy, subject placement, and paint-like quality. "
    "Output JSON with: match_score (1-10), discrepancies (list), suggestion (one sentence)."
)

ARCHITECT_CORRECTION_PROMPT = (
    "You are the Architect for Flise. You have a previous prompt, a generated image, "
    "and new feedback. Create a NEW prompt that keeps the core subjects but fixes "
    "the specific issues mentioned. Do not start over; evolve the image."
)


@dataclass
class CritiqueResult:
    match_score: int
    discrepancies: list[str]
    suggestion: str


class FliseEngine:
    """Pipeline placeholders for Architect, Artist, and Critic.

    Replace internals with real Ollama and Stable Diffusion local API calls.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434") -> None:
        self.ollama_url = ollama_url

    def refine_prompt(self, user_prompt: str, style: str, palette: str) -> str:
        """The Architect: expands a short user brief into a richer generation prompt."""
        return (
            f"{user_prompt.strip()} | style={style} | palette={palette} | "
            "minimalist vector-painting mood, soft Scandinavian lighting, "
            "balanced composition, refined texture guidance"
        )

    def build_correction_prompt(
        self,
        previous_prompt: str,
        critic_feedback: CritiqueResult,
        user_delta: str,
    ) -> str:
        """Performs a delta update rather than replacing the prompt entirely."""
        return (
            f"{previous_prompt}. "
            f"Correction focus: {critic_feedback.suggestion}. "
            f"User refinement: {user_delta.strip() or 'Improve realism and edge coherence.'} "
            "Keep the same core subject while updating only the requested visual traits."
        )

    def generate_image(self, prompt: str, crop_mode: str) -> dict[str, Any]:
        """The Artist: placeholder for local Stable Diffusion endpoint call."""
        seed = random.randint(10_000, 99_999)
        return {
            "seed": seed,
            "image_path": "",
            "meta": {
                "prompt": prompt,
                "crop_mode": crop_mode,
                "provider": "stable-diffusion-placeholder",
            },
        }

    def critic_review(self, user_intent: str, generated_prompt: str, image_path: str) -> CritiqueResult:
        """The Critic: placeholder for a local VLM/Ollama analysis pass."""
        del generated_prompt, image_path
        intent = user_intent.lower()

        if "blue" in intent:
            return CritiqueResult(
                match_score=6,
                discrepancies=["Primary hues may drift away from requested cool blue direction."],
                suggestion="Increase blue dominance and reduce warm highlight bleed.",
            )

        return CritiqueResult(
            match_score=7,
            discrepancies=["Texture could be more paint-like.", "Lighting may appear slightly synthetic."],
            suggestion="Use softer natural lighting and more visible brush-like texture.",
        )

    def call_ollama_chat(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """Placeholder for Ollama chat request.

        Example payload target: POST /api/chat
        {
            "model": "llama3.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": false
        }
        """
        del model, system_prompt, user_prompt
        return "{}"
