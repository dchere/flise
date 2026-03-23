from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine import CritiqueResult, FliseEngine
from mason import the_mason_vectorize


class PipelineState(Enum):
    INPUT = auto()
    GENERATION = auto()
    CRITIQUE = auto()
    REVIEW = auto()
    VECTORIZATION = auto()


@dataclass
class HistoryItem:
    prompt: str
    seed: int
    image_path: str
    critique: CritiqueResult


class FliseStateMachine:
    def __init__(self) -> None:
        self.state = PipelineState.INPUT

    def set_state(self, new_state: PipelineState) -> None:
        self.state = new_state


class RefinementTray(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("RefinementTray")

        layout = QVBoxLayout(self)

        self.ai_critique_label = QLabel("AI Analysis: Waiting for critique...")
        self.ai_critique_label.setObjectName("Subtle")

        self.user_correction = QLineEdit()
        self.user_correction.setPlaceholderText(
            "Tell Flise what to change (e.g., 'More blue', 'Smoother edges')..."
        )

        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Accept & Vectorize")
        self.btn_refine = QPushButton("Refine & Regenerate")
        self.btn_retry = QPushButton("Retry")
        self.btn_retry.setObjectName("Secondary")
        self.btn_step_back = QPushButton("Step Back")
        self.btn_step_back.setObjectName("Secondary")

        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_refine)
        btn_layout.addWidget(self.btn_retry)
        btn_layout.addWidget(self.btn_step_back)

        layout.addWidget(self.ai_critique_label)
        layout.addWidget(self.user_correction)
        layout.addLayout(btn_layout)


class FliseMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Flise - Collaborative Artisan")
        self.resize(1280, 820)

        self.engine = FliseEngine()
        self.machine = FliseStateMachine()
        self.history: list[HistoryItem] = []

        self.current_prompt = ""
        self.current_intent = ""
        self.current_image_path = ""
        self.current_critique = CritiqueResult(7, ["No critique yet."], "Ready for analysis.")

        self._build_ui()
        self._wire_events()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        main_row = QHBoxLayout()
        main_row.setSpacing(18)

        self.sidebar = self._build_sidebar()
        main_row.addWidget(self.sidebar, 0)

        self.content_panel = self._build_content_panel()
        main_row.addWidget(self.content_panel, 1)

        root_layout.addLayout(main_row, 1)

        bottom_row = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Custom requirements and refinement prompts...")
        self.btn_generate = QPushButton("Generate")
        bottom_row.addWidget(self.prompt_input, 1)
        bottom_row.addWidget(self.btn_generate, 0)
        root_layout.addLayout(bottom_row)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Flise Controls")
        header.setObjectName("Header")
        layout.addWidget(header)

        layout.addWidget(QLabel("Style"))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Nordic Minimalist",
            "Soft Watercolor",
            "Bold Gouache",
            "Muted Poster",
        ])
        layout.addWidget(self.style_combo)

        layout.addWidget(QLabel("Cropping"))
        self.crop_combo = QComboBox()
        self.crop_combo.addItems(["Original", "Square", "Portrait", "Landscape"])
        layout.addWidget(self.crop_combo)

        layout.addWidget(QLabel("Palette"))
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(["Muted", "Cold Coast", "Warm Brick", "Forest Fog"])
        layout.addWidget(self.palette_combo)

        layout.addWidget(QLabel("Grain Size"))
        self.grain_slider = QSlider(Qt.Orientation.Horizontal)
        self.grain_slider.setRange(1, 100)
        self.grain_slider.setValue(36)
        layout.addWidget(self.grain_slider)

        self.grain_value = QLabel("36")
        self.grain_value.setObjectName("Subtle")
        layout.addWidget(self.grain_value)

        layout.addStretch(1)
        return sidebar

    def _build_content_panel(self) -> QWidget:
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(12)

        top_actions = QHBoxLayout()
        self.btn_show_generation = QPushButton("Generation View")
        self.btn_show_generation.setObjectName("Secondary")
        self.btn_show_vector = QPushButton("Vector View")
        self.btn_show_vector.setObjectName("Secondary")
        top_actions.addWidget(self.btn_show_generation)
        top_actions.addWidget(self.btn_show_vector)
        top_actions.addStretch(1)
        panel_layout.addLayout(top_actions)

        self.canvas_frame = QFrame()
        self.canvas_frame.setObjectName("CanvasFrame")
        canvas_layout = QVBoxLayout(self.canvas_frame)
        canvas_layout.setContentsMargins(12, 12, 12, 12)

        self.canvas_stack = QStackedWidget()

        generation_view = QWidget()
        gen_layout = QVBoxLayout(generation_view)
        self.generated_image = QLabel("Generation preview appears here")
        self.generated_image.setObjectName("Canvas")
        self.generated_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.generated_image.setMinimumHeight(440)
        gen_layout.addWidget(self.generated_image)

        vector_view = QWidget()
        vec_layout = QVBoxLayout(vector_view)
        self.svg_preview = QTextEdit()
        self.svg_preview.setReadOnly(True)
        self.svg_preview.setPlaceholderText("Vector SVG output preview")
        vec_layout.addWidget(self.svg_preview)

        self.canvas_stack.addWidget(generation_view)
        self.canvas_stack.addWidget(vector_view)

        canvas_layout.addWidget(self.canvas_stack)
        panel_layout.addWidget(self.canvas_frame, 1)

        self.refinement_tray = RefinementTray()
        panel_layout.addWidget(self.refinement_tray)

        return panel

    def _wire_events(self) -> None:
        self.btn_generate.clicked.connect(self.start_generation)
        self.grain_slider.valueChanged.connect(self._update_grain)
        self.btn_show_generation.clicked.connect(lambda: self.canvas_stack.setCurrentIndex(0))
        self.btn_show_vector.clicked.connect(lambda: self.canvas_stack.setCurrentIndex(1))

        self.refinement_tray.btn_accept.clicked.connect(self.accept_and_vectorize)
        self.refinement_tray.btn_refine.clicked.connect(self.refine_and_regenerate)
        self.refinement_tray.btn_retry.clicked.connect(self.retry_generation)
        self.refinement_tray.btn_step_back.clicked.connect(self.step_back)

    def _update_grain(self, value: int) -> None:
        self.grain_value.setText(str(value))

    def start_generation(self) -> None:
        user_text = self.prompt_input.text().strip()
        if not user_text:
            self.refinement_tray.ai_critique_label.setText("AI Analysis: Add a prompt to start.")
            return

        self.current_intent = user_text
        self.run_generation_cycle(base_prompt=user_text)

    def run_generation_cycle(self, base_prompt: str) -> None:
        self.machine.set_state(PipelineState.GENERATION)

        self.current_prompt = self.engine.refine_prompt(
            user_prompt=base_prompt,
            style=self.style_combo.currentText(),
            palette=self.palette_combo.currentText(),
        )

        artist_result = self.engine.generate_image(
            prompt=self.current_prompt,
            crop_mode=self.crop_combo.currentText(),
        )
        self.current_image_path = artist_result.get("image_path", "")
        seed = int(artist_result.get("seed", 0))

        self._render_generation_preview(seed)

        self.machine.set_state(PipelineState.CRITIQUE)
        self.current_critique = self.engine.critic_review(
            user_intent=self.current_intent,
            generated_prompt=self.current_prompt,
            image_path=self.current_image_path,
        )

        critique_text = (
            f"AI Analysis (score {self.current_critique.match_score}/10): "
            f"{'; '.join(self.current_critique.discrepancies)} "
            f"Suggestion: {self.current_critique.suggestion}"
        )
        self.refinement_tray.ai_critique_label.setText(critique_text)

        self.history.append(
            HistoryItem(
                prompt=self.current_prompt,
                seed=seed,
                image_path=self.current_image_path,
                critique=self.current_critique,
            )
        )

        self.machine.set_state(PipelineState.REVIEW)
        self.canvas_stack.setCurrentIndex(0)

    def _render_generation_preview(self, seed: int) -> None:
        if self.current_image_path and Path(self.current_image_path).exists():
            pixmap = QPixmap(self.current_image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.generated_image.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.generated_image.setPixmap(scaled)
                return

        self.generated_image.setText(
            "Raster generation placeholder\n\n"
            f"Seed: {seed}\n"
            f"Prompt: {self.current_prompt[:180]}"
        )

    def accept_and_vectorize(self) -> None:
        self.machine.set_state(PipelineState.VECTORIZATION)
        grain = max(1, self.grain_slider.value() // 10)

        if self.current_image_path and Path(self.current_image_path).exists():
            try:
                svg = the_mason_vectorize(
                    self.current_image_path,
                    color_count=grain,
                    smoothness=0.01,
                )
            except Exception as exc:  # pragma: no cover
                svg = f"<svg><!-- Mason error: {exc} --></svg>"
        else:
            svg = (
                "<svg viewBox='0 0 640 420' xmlns='http://www.w3.org/2000/svg'>"
                "<rect x='20' y='20' width='600' height='380' fill='#d9d9d9' stroke='#b5b5b5'/>"
                "<text x='40' y='70' fill='#4a4a4a' font-size='22'>Flise Vector Preview Placeholder</text>"
                "</svg>"
            )

        self.svg_preview.setPlainText(svg)
        self.canvas_stack.setCurrentIndex(1)

    def refine_and_regenerate(self) -> None:
        user_delta = self.refinement_tray.user_correction.text().strip()
        correction_prompt = self.engine.build_correction_prompt(
            previous_prompt=self.current_prompt,
            critic_feedback=self.current_critique,
            user_delta=user_delta,
        )
        self.prompt_input.setText(correction_prompt)
        self.run_generation_cycle(base_prompt=correction_prompt)

    def retry_generation(self) -> None:
        fallback = f"{self.current_intent}. {self.current_critique.suggestion}"
        self.prompt_input.setText(fallback)
        self.run_generation_cycle(base_prompt=fallback)

    def step_back(self) -> None:
        if len(self.history) <= 1:
            self.refinement_tray.ai_critique_label.setText("AI Analysis: No earlier iteration available.")
            return

        self.history.pop()
        previous = self.history[-1]

        self.current_prompt = previous.prompt
        self.current_image_path = previous.image_path
        self.current_critique = previous.critique

        self._render_generation_preview(previous.seed)
        self.refinement_tray.ai_critique_label.setText(
            f"AI Analysis (restored {previous.critique.match_score}/10): "
            f"{'; '.join(previous.critique.discrepancies)}"
        )
        self.canvas_stack.setCurrentIndex(0)
        self.machine.set_state(PipelineState.REVIEW)


def load_stylesheet(app: QApplication) -> None:
    qss_path = Path(__file__).with_name("style.qss")
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def main() -> int:
    app = QApplication(sys.argv)
    load_stylesheet(app)

    window = FliseMainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
