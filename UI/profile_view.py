"""
User profile view — with editable photo, bio, and skill level backed by MongoDB.
"""

import os
import shutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTextEdit, QComboBox, QFileDialog, QMessageBox,
    QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QColor

import core.database as db
from utils.styles import PROFILE_CARD_STYLE, COLORS

# Where uploaded profile photos are stored locally
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'profile_photos')


def _make_round_pixmap(path: str, size: int) -> QPixmap:
    """Return a circular pixmap from *path*, scaled to *size*x*size*."""
    src = QPixmap(path)
    if src.isNull():
        src = QPixmap(size, size)
        src.fill(QColor(COLORS['bg_tertiary']))

    src = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                     Qt.TransformationMode.SmoothTransformation)

    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path_obj = QPainterPath()
    path_obj.addEllipse(0, 0, size, size)
    painter.setClipPath(path_obj)
    x = (src.width()  - size) // 2
    y = (src.height() - size) // 2
    painter.drawPixmap(0, 0, src, x, y, size, size)
    painter.end()
    return result


class ProfileView(QWidget):
    def __init__(self, user_id: str, scenarios: list, parent=None):
        """
        Parameters
        ----------
        user_id   : the logged-in user's user_id (from loginUser)
        scenarios : list of scenario dicts (from core/data.py)
        """
        super().__init__(parent)
        self.user_id = user_id
        self.scenarios = scenarios
        self._photo_path = ''
        self.setup_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def setup_ui(self):
        user = db.getUser(self.user_id)

        outer = QVBoxLayout()
        outer.setContentsMargins(40, 30, 40, 30)
        outer.setSpacing(25)

        # ── Page title ────────────────────────────────────────────────
        title = QLabel("Profile")
        title.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        outer.addWidget(title)

        # ── Scrollable body ───────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(20)

        # ── Photo + name card ─────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(PROFILE_CARD_STYLE)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(24)

        # Avatar column
        avatar_col = QVBoxLayout()
        avatar_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._avatar_label = QLabel()
        self._avatar_label.setFixedSize(100, 100)
        self._avatar_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._avatar_label.setToolTip("Click to change photo")
        self._avatar_label.mousePressEvent = lambda _e: self._pick_photo()
        self._refresh_avatar(user.get('profile_photo', ''))
        avatar_col.addWidget(self._avatar_label)

        change_photo_btn = QPushButton("Change Photo")
        change_photo_btn.setFont(QFont('Arial', 9))
        change_photo_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['accent_blue']};
                border: none;
                padding: 2px 0;
            }}
            QPushButton:hover {{ color: {COLORS['accent_blue_hover']}; }}
        """)
        change_photo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_photo_btn.clicked.connect(self._pick_photo)
        avatar_col.addWidget(change_photo_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        card_layout.addLayout(avatar_col)

        # Name + skill level column
        info_col = QVBoxLayout()
        info_col.setSpacing(10)
        info_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        username_lbl = QLabel(user.get('username', ''))
        username_lbl.setFont(QFont('Arial', 22, QFont.Weight.Bold))
        username_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        info_col.addWidget(username_lbl)

        role_lbl = QLabel("Cybersecurity Student")
        role_lbl.setFont(QFont('Arial', 12))
        role_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_col.addWidget(role_lbl)

        # Skill level selector
        skill_row = QHBoxLayout()
        skill_lbl = QLabel("Skill Level:")
        skill_lbl.setFont(QFont('Arial', 11))
        skill_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        skill_row.addWidget(skill_lbl)

        self._skill_combo = QComboBox()
        self._skill_combo.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        self._skill_combo.setCurrentText(user.get('skill_level', 'Beginner'))
        self._skill_combo.setFont(QFont('Arial', 11))
        self._skill_combo.setFixedWidth(160)
        self._skill_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 10px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent_blue']};
            }}
        """)
        skill_row.addWidget(self._skill_combo)
        skill_row.addStretch()
        info_col.addLayout(skill_row)

        card_layout.addLayout(info_col, stretch=1)
        body_layout.addWidget(card)

        # ── Bio / description card ─────────────────────────────────────
        bio_card = QFrame()
        bio_card.setStyleSheet(PROFILE_CARD_STYLE)
        bio_layout = QVBoxLayout(bio_card)
        bio_layout.setContentsMargins(25, 20, 25, 20)
        bio_layout.setSpacing(10)

        bio_title = QLabel("Bio")
        bio_title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        bio_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        bio_layout.addWidget(bio_title)

        self._bio_edit = QTextEdit()
        # MongoDB field is called "description" — map it here
        self._bio_edit.setPlainText(user.get('description', '') or '')
        self._bio_edit.setPlaceholderText(
            "Tell us about yourself — your goals, background, or what you're learning…"
        )
        self._bio_edit.setFont(QFont('Arial', 11))
        self._bio_edit.setFixedHeight(110)
        self._bio_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            QTextEdit:focus {{
                border: 1px solid {COLORS['accent_blue']};
            }}
        """)
        bio_layout.addWidget(self._bio_edit)
        body_layout.addWidget(bio_card)

        # ── Stats row ─────────────────────────────────────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        completed  = db.getCompletedScenarios(self.user_id)
        skill_txt  = user.get('skill_level', 'Beginner')

        for label, value in [
            ("🏆  Completed Scenarios", f"{len(completed)} / {len(self.scenarios)}"),
            ("🛡️  Skill Level",         skill_txt),
        ]:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(PROFILE_CARD_STYLE)
            stat_inner = QVBoxLayout(stat_frame)
            stat_inner.setContentsMargins(20, 18, 20, 18)

            lbl = QLabel(label)
            lbl.setFont(QFont('Arial', 10))
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_inner.addWidget(lbl)

            val = QLabel(value)
            val.setFont(QFont('Arial', 20, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {COLORS['text_primary']};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_inner.addWidget(val)

            if "Skill Level" in label:
                self._skill_stat_label = val

            stats_layout.addWidget(stat_frame)

        body_layout.addLayout(stats_layout)

        # ── Save button ───────────────────────────────────────────────
        save_btn = QPushButton("💾  Save Profile")
        save_btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        save_btn.setFixedHeight(46)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue_hover']};
            }}
        """)
        save_btn.clicked.connect(self._save_profile)
        body_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        body_layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)
        self.setLayout(outer)

    # ------------------------------------------------------------------
    # Photo helpers
    # ------------------------------------------------------------------

    def _pick_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Profile Photo",
            os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return

        os.makedirs(PHOTOS_DIR, exist_ok=True)
        ext  = os.path.splitext(path)[1]
        dest = os.path.join(PHOTOS_DIR, f"{self.user_id}{ext}")
        shutil.copy2(path, dest)

        self._photo_path = dest
        self._refresh_avatar(dest)

    def _refresh_avatar(self, photo_path: str):
        self._photo_path = photo_path or ''
        if photo_path and os.path.isfile(photo_path):
            pix = _make_round_pixmap(photo_path, 100)
        else:
            pix = QPixmap(100, 100)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(COLORS['bg_tertiary']))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, 100, 100)
            painter.setPen(QColor(COLORS['text_secondary']))
            painter.setFont(QFont('Arial', 36, QFont.Weight.Bold))
            painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "👤")
            painter.end()
        self._avatar_label.setPixmap(pix)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save_profile(self):
        # "description" is the MongoDB field name; "profile_photo" matches addUser
        db.updateProfile(
            self.user_id,
            description=self._bio_edit.toPlainText().strip(),
            skill_level=self._skill_combo.currentText(),
            profile_photo=self._photo_path,
        )

        # Instantly update the stat badge so the user sees the change
        if hasattr(self, '_skill_stat_label'):
            self._skill_stat_label.setText(self._skill_combo.currentText())

        QMessageBox.information(self, "Profile Saved", "Your profile has been updated ✅")
