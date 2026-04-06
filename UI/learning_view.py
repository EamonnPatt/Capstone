"""
Learning resources view
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                              QLabel, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.data import LEARNING_MODULES
from utils.styles import COLORS, FONT, MODULE_ACCENT_COLORS, get_module_card_style


class LearningView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 28, 36, 28)
        outer.setSpacing(6)

        # ── Page header ───────────────────────────────────────────────
        header = QLabel("Learning Resources")
        header.setFont(QFont(FONT, 26, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        outer.addWidget(header)

        subtitle = QLabel("Study the theory before diving into the scenarios")
        subtitle.setFont(QFont(FONT, 12))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 12px;")
        outer.addWidget(subtitle)

        # ── Scrollable card list ──────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 4, 0, 4)

        for i, module in enumerate(LEARNING_MODULES):
            layout.addWidget(self._build_card(module, i))

        layout.addStretch()
        scroll.setWidget(scroll_widget)
        outer.addWidget(scroll)

    # ── Card builder ──────────────────────────────────────────────────────────

    def _build_card(self, module: dict, index: int) -> QFrame:
        accent = MODULE_ACCENT_COLORS.get(module['id'], COLORS['accent_blue'])

        card = QFrame()
        card.setStyleSheet(get_module_card_style(accent))
        card.setMinimumHeight(110)

        row = QHBoxLayout(card)
        row.setContentsMargins(22, 20, 22, 20)
        row.setSpacing(18)

        # ── Icon badge ────────────────────────────────────────────────
        icon_lbl = QLabel(module['icon'])
        icon_lbl.setFont(QFont(FONT, 22))
        icon_lbl.setFixedSize(52, 52)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background-color: {accent}22;
            border-radius: 12px;
            border: 1px solid {accent}44;
        """)
        row.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        # ── Text content ──────────────────────────────────────────────
        content = QVBoxLayout()
        content.setSpacing(6)
        content.setContentsMargins(0, 0, 0, 0)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title = QLabel(module['name'])
        title.setFont(QFont(FONT, 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_row.addWidget(title)
        title_row.addStretch()

        num_lbl = QLabel(f"MODULE {index + 1:02d}")
        num_lbl.setFont(QFont(FONT, 8, QFont.Weight.Bold))
        num_lbl.setStyleSheet(f"color: {accent}; letter-spacing: 1px;")
        title_row.addWidget(num_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        content.addLayout(title_row)

        desc = QLabel(module['description'])
        desc.setFont(QFont(FONT, 10))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        content.addWidget(desc)

        # Topic chips using rich text
        topics = module.get('topics', [])
        if topics:
            chips_html = "&nbsp; ".join(
                f'<span style="'
                f'background-color:{COLORS["bg_tertiary"]};'
                f'color:{COLORS["text_secondary"]};'
                f'border:1px solid {COLORS["border"]};'
                f'border-radius:8px;'
                f'padding:2px 10px;'
                f'font-size:10px;'
                f'">{topic}</span>'
                for topic in topics
            )
            chips_lbl = QLabel(chips_html)
            chips_lbl.setTextFormat(Qt.TextFormat.RichText)
            chips_lbl.setWordWrap(True)
            chips_lbl.setStyleSheet("color: transparent;")
            content.addWidget(chips_lbl)

        row.addLayout(content, stretch=1)
        return card
