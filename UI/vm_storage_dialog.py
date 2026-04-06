"""
VM Storage Setup Dialog
"""

import os
import json
from pathlib import Path

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFileDialog,
                              QProgressBar, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.styles import COLORS, LAUNCH_BUTTON_STYLE

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}


def save_config(data: dict):
    existing = load_config()
    existing.update(data)
    CONFIG_PATH.write_text(json.dumps(existing, indent=2))


def get_vagrant_home():
    return load_config().get("vagrant_home")


def apply_vagrant_home(path: str):
    os.environ["VAGRANT_HOME"] = path
    save_config({"vagrant_home": path})


class VMStorageDialog(QDialog):
    def __init__(self, scenario_name: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VM Storage Location")
        self.setMinimumWidth(580)
        self.setModal(True)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']}; color: {COLORS['text_primary']};")

        layout = QVBoxLayout()
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(0)

        title = QLabel("Choose VM Storage Location")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)
        layout.addSpacing(8)

        if scenario_name:
            subtitle_text = (
                f"Virtual machines for <b>{scenario_name}</b> need to be downloaded "
                "and stored on your machine. Choose a drive with enough free space."
            )
        else:
            subtitle_text = "VM images can be several gigabytes. Choose a drive with at least 15 GB free."
        subtitle = QLabel(subtitle_text)
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        note = QLabel("Both the Vagrant box cache and VirtualBox VM files will be stored on the chosen drive.")
        note.setFont(QFont("Arial", 10))
        note.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addSpacing(12)

        # Disk space requirements box
        req_frame = QFrame()
        req_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-radius: 8px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        req_layout = QVBoxLayout()
        req_layout.setContentsMargins(16, 12, 16, 12)
        req_layout.setSpacing(4)
        req_title = QLabel("Approximate download sizes")
        req_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        req_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        req_layout.addWidget(req_title)
        for vm, size in [("Linux Kali", "~4 GB"), ("Linux Ubuntu", "~2 GB"), ("Windows 11", "~20 GB (manual setup)")]:
            lbl = QLabel(f"  {vm}  —  {size}")
            lbl.setFont(QFont("Arial", 10))
            lbl.setStyleSheet(f"color: {COLORS['text_tertiary']};")
            req_layout.addWidget(lbl)
        req_frame.setLayout(req_layout)
        layout.addWidget(req_frame)
        layout.addSpacing(20)

        drives_label = QLabel("Available Drives")
        drives_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        drives_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(drives_label)
        layout.addSpacing(10)

        self.drive_cards_layout = QVBoxLayout()
        self.drive_cards_layout.setSpacing(8)
        self._populate_drive_cards()
        layout.addLayout(self.drive_cards_layout)
        layout.addSpacing(24)

        path_label = QLabel("Storage folder")
        path_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        path_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(path_label)
        layout.addSpacing(6)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(r"e.g. D:\.vagrant.d")
        self.path_input.setFont(QFont("Arial", 10))
        self.path_input.setMinimumHeight(38)
        self.path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 12px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['accent_blue']}; }}
        """)
        saved = get_vagrant_home()
        self.path_input.setText(saved or self._best_default_path())
        path_row.addWidget(self.path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.setFont(QFont("Arial", 10))
        browse_btn.setMinimumHeight(38)
        browse_btn.setMinimumWidth(90)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border_hover']}; }}
        """)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)
        layout.addSpacing(6)

        self.path_hint = QLabel("")
        self.path_hint.setFont(QFont("Arial", 9))
        self.path_hint.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        layout.addWidget(self.path_hint)
        self._update_hint()
        self.path_input.textChanged.connect(self._update_hint)
        layout.addSpacing(28)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Arial", 11))
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(10)

        self.confirm_btn = QPushButton("Save & Continue")
        self.confirm_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.confirm_btn.setMinimumHeight(42)
        self.confirm_btn.setMinimumWidth(150)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet(LAUNCH_BUTTON_STYLE)
        self.confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(self.confirm_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _best_default_path(self) -> str:
        """Return a default path on the drive with the most free space."""
        best_letter, best_free = "C", -1.0
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                try:
                    import shutil
                    free = shutil.disk_usage(path).free / 1e9
                    if free > best_free:
                        best_free, best_letter = free, letter
                except Exception:
                    pass
        return f"{best_letter}:\\.vagrant.d"

    def _populate_drive_cards(self):
        for drive in self._get_drives():
            self.drive_cards_layout.addWidget(self._make_drive_card(drive))

    def _get_drives(self):
        import shutil
        drives = []
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                try:
                    usage = shutil.disk_usage(path)
                    drives.append({
                        "letter": letter,
                        "path": path,
                        "free_gb":  usage.free  / 1e9,
                        "total_gb": usage.total / 1e9,
                        "used_pct": usage.used  / usage.total,
                    })
                except Exception:
                    pass
        return drives

    def _make_drive_card(self, drive):
        free = drive["free_gb"]
        ok   = free >= 15

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {'#10b981' if ok else COLORS['border']};
                border-radius: 8px;
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        row = QHBoxLayout()
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(16)

        letter_lbl = QLabel(f"{drive['letter']}:")
        letter_lbl.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        letter_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 30px;")
        row.addWidget(letter_lbl)

        bar_col = QVBoxLayout()
        bar_col.setSpacing(4)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(drive["used_pct"] * 100))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar_color = COLORS["danger"] if drive["used_pct"] > 0.9 else COLORS["accent_blue"]
        bar.setStyleSheet(f"""
            QProgressBar {{ background-color: {COLORS['bg_tertiary']}; border-radius: 4px; border: none; }}
            QProgressBar::chunk {{ background-color: {bar_color}; border-radius: 4px; }}
        """)
        bar_col.addWidget(bar)

        nums = QLabel(f"{free:.1f} GB free of {drive['total_gb']:.0f} GB")
        nums.setFont(QFont("Arial", 9))
        nums.setStyleSheet(f"color: {COLORS['text_secondary']};")
        bar_col.addWidget(nums)
        row.addLayout(bar_col, stretch=1)

        badge = QLabel("Recommended" if ok else "Low space")
        badge.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        badge.setStyleSheet(f"color: {COLORS['success'] if ok else COLORS['warning']};")
        row.addWidget(badge)

        card.setLayout(row)
        default_path = f"{drive['letter']}:\\.vagrant.d"
        card.mousePressEvent = lambda e, p=default_path: self.path_input.setText(p)
        return card

    def _update_hint(self):
        path = self.path_input.text().strip()
        if not path:
            self.path_hint.setText("")
            return
        try:
            import shutil
            drive = Path(path).anchor
            free  = shutil.disk_usage(drive).free / 1e9
            color = COLORS["success"] if free >= 15 else COLORS["warning"]
            self.path_hint.setText(f"{free:.1f} GB free on {drive}")
            self.path_hint.setStyleSheet(f"color: {color};")
        except Exception:
            self.path_hint.setText("")

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose VM storage folder", self.path_input.text() or "C:\\")
        if folder:
            self.path_input.setText(str(Path(folder) / ".vagrant.d"))

    def _confirm(self):
        path = self.path_input.text().strip()
        if not path:
            self.path_hint.setText("Please enter a folder path.")
            self.path_hint.setStyleSheet(f"color: {COLORS['danger']};")
            return
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.path_hint.setText(f"Could not create folder: {e}")
            self.path_hint.setStyleSheet(f"color: {COLORS['danger']};")
            return
        apply_vagrant_home(path)
        self.accept()

    @staticmethod
    def ensure_configured(parent=None, scenario_name: str = None) -> bool:
        saved = get_vagrant_home()
        if saved:
            # Validate the drive still exists before trusting the saved path
            drive = Path(saved).anchor
            if os.path.exists(drive):
                apply_vagrant_home(saved)
                return True
            # Drive is gone — clear the stale config and fall through to the dialog
            save_config({"vagrant_home": None})
        dlg = VMStorageDialog(scenario_name=scenario_name, parent=parent)
        return dlg.exec() == QDialog.DialogCode.Accepted
