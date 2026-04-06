"""
User profile view
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from utils.styles import PROFILE_CARD_STYLE, PROGRESS_BAR_STYLE, COLORS, FONT


def _skill_level(completed: int, total: int) -> tuple[str, str]:
    """Return (label, color) based on completion count."""
    ratio = completed / max(total, 1)
    if ratio == 0:
        return "Beginner", COLORS['text_tertiary']
    if ratio < 0.4:
        return "Novice", COLORS['warning']
    if ratio < 0.8:
        return "Intermediate", COLORS['accent_blue']
    return "Advanced", COLORS['success']


class ProfileView(QWidget):
    def __init__(self, user_data, scenarios, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.scenarios = scenarios
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        completed_ids = self.user_data.get('completed_scenarios', [])
        total = len(self.scenarios)
        done  = len(completed_ids)

        # ── Profile header card ───────────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet(PROFILE_CARD_STYLE)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 28, 30, 28)
        header_layout.setSpacing(10)

        # Top row: avatar + name + skill badge
        top_row = QHBoxLayout()
        top_row.setSpacing(18)

        avatar = QLabel("👤")
        avatar.setFont(QFont(FONT, 30))
        avatar.setFixedSize(64, 64)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {COLORS['bg_tertiary']};
            border-radius: 32px;
            border: 2px solid {COLORS['border_hover']};
        """)
        top_row.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignVCenter)

        name_col = QVBoxLayout()
        name_col.setSpacing(4)

        username = QLabel(self.user_data.get('username', 'Student'))
        username.setFont(QFont(FONT, 22, QFont.Weight.Bold))
        username.setStyleSheet(f"color: {COLORS['text_primary']};")
        name_col.addWidget(username)

        role = QLabel("Cybersecurity Student")
        role.setFont(QFont(FONT, 11))
        role.setStyleSheet(f"color: {COLORS['text_secondary']};")
        name_col.addWidget(role)

        top_row.addLayout(name_col)
        top_row.addStretch()

        skill_label, skill_color = _skill_level(done, total)
        skill_badge = QLabel(f"  {skill_label}  ")
        skill_badge.setFont(QFont(FONT, 10, QFont.Weight.Bold))
        skill_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        skill_badge.setFixedHeight(28)
        skill_badge.setStyleSheet(f"""
            background-color: {skill_color}22;
            color: {skill_color};
            border: 1px solid {skill_color}66;
            border-radius: 14px;
            padding: 0 14px;
        """)
        top_row.addWidget(skill_badge, alignment=Qt.AlignmentFlag.AlignVCenter)

        header_layout.addLayout(top_row)

        # Progress bar
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)

        prog_lbl = QLabel(f"Scenario Progress")
        prog_lbl.setFont(QFont(FONT, 10))
        prog_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        prog_row.addWidget(prog_lbl)

        prog_count = QLabel(f"{done} / {total}")
        prog_count.setFont(QFont(FONT, 10, QFont.Weight.Bold))
        prog_count.setStyleSheet(f"color: {COLORS['text_primary']};")
        prog_row.addWidget(prog_count, alignment=Qt.AlignmentFlag.AlignRight)

        header_layout.addLayout(prog_row)

        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(total)
        bar.setValue(done)
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setStyleSheet(PROGRESS_BAR_STYLE)
        header_layout.addWidget(bar)

        layout.addWidget(header_frame)

        # ── Stats row ─────────────────────────────────────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        stats = [
            ("🏆", "Completed", f"{done}/{total}", COLORS['success'] if done > 0 else COLORS['text_secondary']),
            ("📚", "Modules",   str(self.user_data.get('learning_modules_completed', 0)), COLORS['accent_blue']),
            ("🛡️", "Skill",    skill_label, skill_color),
        ]

        for icon, label, value, color in stats:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(PROFILE_CARD_STYLE)

            stat_layout = QVBoxLayout(stat_frame)
            stat_layout.setContentsMargins(20, 20, 20, 20)
            stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.setSpacing(6)

            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont(FONT, 20))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(icon_lbl)

            val_lbl = QLabel(value)
            val_lbl.setFont(QFont(FONT, 20, QFont.Weight.Bold))
            val_lbl.setStyleSheet(f"color: {color};")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(val_lbl)

            label_lbl = QLabel(label)
            label_lbl.setFont(QFont(FONT, 10))
            label_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            label_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(label_lbl)

            stats_layout.addWidget(stat_frame)

        layout.addLayout(stats_layout)

        # ── Completed scenarios list ──────────────────────────────────
        if completed_ids:
            comp_frame = QFrame()
            comp_frame.setStyleSheet(PROFILE_CARD_STYLE)
            comp_layout = QVBoxLayout(comp_frame)
            comp_layout.setContentsMargins(24, 20, 24, 20)
            comp_layout.setSpacing(12)

            comp_title = QLabel("Completed Scenarios")
            comp_title.setFont(QFont(FONT, 13, QFont.Weight.Bold))
            comp_title.setStyleSheet(f"color: {COLORS['text_primary']};")
            comp_layout.addWidget(comp_title)

            id_to_scenario = {s['id']: s for s in self.scenarios}
            for sid in completed_ids:
                scenario = id_to_scenario.get(sid)
                if not scenario:
                    continue

                row = QHBoxLayout()
                row.setSpacing(12)

                check = QLabel("✓")
                check.setFont(QFont(FONT, 11, QFont.Weight.Bold))
                check.setFixedSize(26, 26)
                check.setAlignment(Qt.AlignmentFlag.AlignCenter)
                check.setStyleSheet(f"""
                    background-color: {COLORS['success']}22;
                    color: {COLORS['success']};
                    border: 1px solid {COLORS['success']}44;
                    border-radius: 13px;
                """)
                row.addWidget(check, alignment=Qt.AlignmentFlag.AlignVCenter)

                name_lbl = QLabel(scenario['name'])
                name_lbl.setFont(QFont(FONT, 11))
                name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
                row.addWidget(name_lbl)

                from core.data import get_difficulty_color
                diff_color = get_difficulty_color(scenario['difficulty'])
                diff_lbl = QLabel(scenario['difficulty'])
                diff_lbl.setFont(QFont(FONT, 9, QFont.Weight.Bold))
                diff_lbl.setStyleSheet(f"""
                    background-color: {diff_color}33;
                    color: {diff_color};
                    border-radius: 8px;
                    padding: 2px 10px;
                """)
                row.addWidget(diff_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
                row.addStretch()

                comp_layout.addLayout(row)

            layout.addWidget(comp_frame)

        layout.addStretch()
