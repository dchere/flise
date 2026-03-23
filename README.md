# Flise Skeleton

Initial PyQt6 skeleton for Flise, a desktop app for prompt refinement, image generation, critique/review, and SVG vectorization.

## Structure

- main.py: PyQt6 shell, state machine wiring, review loop, and history buffer.
- engine.py: Architect, Artist, and Critic placeholders (including Ollama call stub).
- mason.py: OpenCV + K-Means based raster to SVG conversion function.
- style.qss: Minimal visual theme.

## Run

1. Create and activate a Python 3.11+ environment.
2. Install dependencies:

   pip install -r requirements.txt

3. Start the app:

   python main.py

## Notes

- Artist and Critic currently return placeholder data.
- Mason works with a real raster file path once image generation is connected.
