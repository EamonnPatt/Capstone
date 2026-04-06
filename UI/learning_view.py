"""
Learning resources view — with clickable lesson cards that open slideshow windows
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.data import LEARNING_MODULES
from utils.styles import MODULE_CARD_STYLE, COLORS
from UI.lesson_view import LessonWindow


class LearningView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._open_lessons = []   # keep references alive
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(40, 30, 40, 30)
        outer.setSpacing(20)

        header = QLabel("Learning Resources")
        header.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        outer.addWidget(header)

        subtitle = QLabel("Study the theory before diving into the scenarios")
        subtitle.setFont(QFont('Arial', 13))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        outer.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        for module in LEARNING_MODULES:
            frame = QFrame()
            frame.setStyleSheet(MODULE_CARD_STYLE)

            module_layout = QVBoxLayout()
            module_layout.setContentsMargins(25, 20, 25, 20)
            module_layout.setSpacing(10)

            # Title row
            title_row = QHBoxLayout()
            title = QLabel(f"{module['icon']}  {module['name']}")
            title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {COLORS['text_primary']};")
            title_row.addWidget(title)
            title_row.addStretch()

            # "Open Lesson" button
            open_btn = QPushButton("📖  Open Lesson")
            open_btn.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            open_btn.setFixedHeight(34)
            open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            open_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_blue']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_blue_hover']};
                }}
            """)
            open_btn.clicked.connect(lambda checked, mid=module['id']: self._open_lesson(mid))
            title_row.addWidget(open_btn)

            module_layout.addLayout(title_row)

            desc = QLabel(module['description'])
            desc.setFont(QFont('Arial', 11))
            desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
            desc.setWordWrap(True)
            module_layout.addWidget(desc)

            # Topics list
            topics = module.get('topics', [])
            if topics:
                topics_label = QLabel("Topics covered:")
                topics_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
                topics_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
                module_layout.addWidget(topics_label)

                topics_text = "   •  " + "\n   •  ".join(topics)
                topics_body = QLabel(topics_text)
                topics_body.setFont(QFont('Arial', 10))
                topics_body.setStyleSheet(f"color: {COLORS['text_secondary']};")
                module_layout.addWidget(topics_body)

            frame.setLayout(module_layout)
            layout.addWidget(frame)

        layout.addStretch()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        outer.addWidget(scroll)

        self.setLayout(outer)

    def _open_lesson(self, module_id):
        window = LessonWindow(module_id)
        window.closed.connect(lambda w=window: self._open_lessons.remove(w) if w in self._open_lessons else None)
        self._open_lessons.append(window)
        window.show()
        window.raise_()
        window.activateWindow()