"""
Flag submission dialog — lets users enter the flag they found in a scenario VM
to mark it as complete and save progress to their profile.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from utils.styles import COLORS


class FlagSubmitDialog(QDialog):
    """
    Modal dialog for submitting a scenario completion flag.

    The dialog validates the entered flag against scenario['flag'] (case-insensitive).
    It also accepts the flag with a "Flag: " prefix, matching what the VMs write
    to their hidden flag files (e.g. `cat .hidden_flag` prints "Flag: CL-BASICS-COMPLETE").

    On success the dialog closes with Accepted; the caller should then call
    core.progress.mark_scenario_complete().
    """

    def __init__(self, scenario: dict, already_complete: bool = False, parent=None):
        super().__init__(parent)
        self.scenario = scenario
        self.already_complete = already_complete
        self.setWindowTitle(f"Submit Flag — {scenario['name']}")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Title
        title = QLabel(f"Submit Flag: {self.scenario['name']}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Already-complete banner
        if self.already_complete:
            banner = QLabel("✓  You have already completed this scenario.")
            banner.setFont(QFont("Arial", 11))
            banner.setStyleSheet(f"""
                color: {COLORS['success']};
                background-color: #0d2b1e;
                border: 1px solid {COLORS['success']};
                border-radius: 6px;
                padding: 8px 12px;
            """)
            layout.addWidget(banner)

        # Hint
        hint_text = scenario_hint(self.scenario)
        hint = QLabel(hint_text)
        hint.setFont(QFont("Arial", 11))
        hint.setStyleSheet(f"color: {COLORS['text_secondary']};")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Input
        self.flag_input = QLineEdit()
        self.flag_input.setPlaceholderText("Enter flag here…  e.g. CL-BASICS-COMPLETE")
        self.flag_input.setFont(QFont("Courier New", 12))
        self.flag_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_blue']};
            }}
        """)
        self.flag_input.returnPressed.connect(self._submit)
        layout.addWidget(self.flag_input)

        # Result label (hidden until first attempt)
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        layout.addWidget(self.result_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Arial", 11))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border_hover']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.submit_btn = QPushButton("Submit Flag")
        self.submit_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setDefault(True)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
            }}
            QPushButton:hover {{ background-color: {COLORS['accent_blue_hover']}; }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_tertiary']};
            }}
        """)
        self.submit_btn.clicked.connect(self._submit)
        btn_row.addWidget(self.submit_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _normalize(self, text: str) -> str:
        """Strip optional 'Flag: ' prefix and whitespace, then uppercase."""
        stripped = text.strip()
        if stripped.upper().startswith("FLAG: "):
            stripped = stripped[6:].strip()
        return stripped.upper()

    def _submit(self):
        entered = self.flag_input.text()
        correct = self.scenario.get('flag', '')

        if not entered.strip():
            return

        if self._normalize(entered) == correct.upper():
            self.result_label.setText("✓  Correct! Scenario marked as complete.")
            self.result_label.setStyleSheet(f"color: {COLORS['success']};")
            self.result_label.show()
            self.submit_btn.setEnabled(False)
            self.flag_input.setEnabled(False)
            QTimer.singleShot(1400, self.accept)
        else:
            self.result_label.setText("✗  Incorrect flag — check your answer and try again.")
            self.result_label.setStyleSheet(f"color: {COLORS['danger']};")
            self.result_label.show()
            self.flag_input.selectAll()
            self.flag_input.setFocus()


# ── Helper ────────────────────────────────────────────────────────────────────

def scenario_hint(scenario: dict) -> str:
    """Return the hint text to display in the dialog."""
    hint = scenario.get('flag_hint', '')
    if hint:
        return f"Find the flag hidden in the VM and enter it below.\n\nHint: {hint}"
    return "Find the flag hidden in the scenario VM and enter it below."
