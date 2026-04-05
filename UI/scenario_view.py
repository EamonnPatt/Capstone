"""
Reusable UI widgets — Vagrant-integrated VM controls
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QMessageBox, QApplication,
                              QDialog, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor
from utils.styles import (VM_CONTROL_STYLE, START_BUTTON_STYLE, STOP_BUTTON_STYLE,
                           SCENARIO_ITEM_STYLE, SCENARIO_ITEM_EXPANDED_STYLE,
                           SCENARIO_HEADER_STYLE, SCENARIO_CONTENT_STYLE, COLORS)
from core.data import get_difficulty_color


# ──────────────────────────────────────────────────────────────────────────────
# Signal bridge — lets worker threads safely update Qt widgets
# ──────────────────────────────────────────────────────────────────────────────

class _Signals(QObject):
    output_line  = pyqtSignal(str)
    operation_done = pyqtSignal(bool)
    status_changed = pyqtSignal(str)


# ──────────────────────────────────────────────────────────────────────────────
# Vagrant output dialog
# ──────────────────────────────────────────────────────────────────────────────

class VagrantOutputDialog(QDialog):
    """Floating terminal-style window that streams vagrant output."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 420)
        self.setModal(False)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Courier New", 9))
        self.log.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0d1117;
                color: #58d68d;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.log)

        self.status_label = QLabel("Running…")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)

        self.close_btn = QPushButton("Close")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: none; border-radius: 6px; padding: 8px 20px;
            }}
            QPushButton:enabled:hover {{
                background-color: {COLORS['border_hover']};
            }}
            QPushButton:disabled {{
                color: {COLORS['text_tertiary']};
            }}
        """)
        layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def append_line(self, line: str):
        self.log.append(line)
        self.log.moveCursor(QTextCursor.MoveOperation.End)

    def mark_done(self, success: bool):
        if success:
            self.status_label.setText("✅  Done")
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
        else:
            self.status_label.setText("❌  Failed — check output above")
            self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
        self.close_btn.setEnabled(True)


# ──────────────────────────────────────────────────────────────────────────────
# VM Control widget (Vagrant-backed)
# ──────────────────────────────────────────────────────────────────────────────

class VMControl(QFrame):
    """Individual VM control widget — uses Vagrant for start/stop."""

    def __init__(self, vm_name: str, vm_manager, vagrant_manager=None,
                 scenario_id: str = None, parent=None):
        super().__init__(parent)
        self.vm_name        = vm_name
        self.vm_manager     = vm_manager       # VBoxManage (status polling)
        self.vagrant_manager = vagrant_manager  # Vagrant (lifecycle)
        self.scenario_id    = scenario_id
        self._busy          = False

        self._signals = _Signals()
        self._signals.status_changed.connect(self._apply_status)
        self._signals.output_line.connect(self._on_output)
        self._signals.operation_done.connect(self._on_done)

        self._output_dialog: VagrantOutputDialog | None = None

        self.setup_ui()

        self._timer = QTimer()
        self._timer.timeout.connect(self._poll_status)
        self._timer.start(5000)
        self._poll_status()

    # ── UI ────────────────────────────────────────────────────────────

    def setup_ui(self):
        self.setStyleSheet(VM_CONTROL_STYLE)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)

        self.name_label = QLabel(self.vm_name)
        self.name_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.name_label)

        layout.addStretch()

        self.status_label = QLabel("Checking…")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)

        # Provision / Up button  (replaces plain "Start")
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.start_btn.setStyleSheet(START_BUTTON_STYLE)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._start)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)

    # ── Status polling ────────────────────────────────────────────────

    def _poll_status(self):
        if self._busy:
            return

        if self.vagrant_manager and self.scenario_id:
            state = self.vagrant_manager.get_vm_status(self.scenario_id, self.vm_name)
        else:
            state = self.vm_manager.get_vm_state(self.vm_name)

        self._signals.status_changed.emit(state)

    def _apply_status(self, state: str):
        mapping = {
            "running":     ("● Running",     COLORS["success"],          False, True),
            "poweroff":    ("● Stopped",     COLORS["text_secondary"],   True,  False),
            "not created": ("● Not created", COLORS["text_tertiary"],    True,  False),
            "saved":       ("● Suspended",   COLORS["warning"],          True,  True),
        }
        text, color, can_start, can_stop = mapping.get(
            state, ("● Unknown", COLORS["warning"], True, True)
        )
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.start_btn.setEnabled(can_start and not self._busy)
        self.stop_btn.setEnabled(can_stop and not self._busy)

    # ── Actions ───────────────────────────────────────────────────────

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.start_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(not busy)

    def _open_output_dialog(self, title: str):
        self._output_dialog = VagrantOutputDialog(title, self)
        self._output_dialog.show()

    def _on_output(self, line: str):
        if self._output_dialog:
            self._output_dialog.append_line(line)

    def _on_done(self, success: bool):
        self._set_busy(False)
        if self._output_dialog:
            self._output_dialog.mark_done(success)
        self._poll_status()

    def _start(self):
        if self._busy:
            return

        if self.vagrant_manager and self.scenario_id:
            self._set_busy(True)
            self._open_output_dialog(f"Starting {self.vm_name}")
            self.vagrant_manager.up_async(
                self.scenario_id,
                self.vm_name,
                output_cb=lambda line: self._signals.output_line.emit(line),
                done_cb=lambda ok: self._signals.operation_done.emit(ok),
            )
        else:
            # Fallback to direct VBoxManage
            if self.vm_manager.start_vm(self.vm_name):
                QMessageBox.information(self, "Success",
                                        f"VM '{self.vm_name}' started successfully!")
            else:
                QMessageBox.critical(self, "Error",
                                     f"Failed to start VM '{self.vm_name}'")
            self._poll_status()

    def _stop(self):
        if self._busy:
            return

        if self.vagrant_manager and self.scenario_id:
            self._set_busy(True)
            self._open_output_dialog(f"Stopping {self.vm_name}")
            self.vagrant_manager.halt_async(
                self.scenario_id,
                self.vm_name,
                output_cb=lambda line: self._signals.output_line.emit(line),
                done_cb=lambda ok: self._signals.operation_done.emit(ok),
            )
        else:
            if self.vm_manager.stop_vm(self.vm_name):
                QMessageBox.information(self, "Success",
                                        f"VM '{self.vm_name}' stopped successfully!")
            else:
                QMessageBox.critical(self, "Error",
                                     f"Failed to stop VM '{self.vm_name}'")
            self._poll_status()

    # ── Cleanup ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)


# ──────────────────────────────────────────────────────────────────────────────
# Scenario Item (unchanged logic, passes vagrant_manager through)
# ──────────────────────────────────────────────────────────────────────────────

class ScenarioItem(QFrame):
    """Expandable scenario item."""

    def __init__(self, scenario, vm_manager, vagrant_manager=None, parent=None):
        super().__init__(parent)
        self.scenario        = scenario
        self.vm_manager      = vm_manager
        self.vagrant_manager = vagrant_manager
        self.parent_window   = parent
        self.is_expanded     = False
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(SCENARIO_ITEM_STYLE)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        self.header = QFrame()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet(SCENARIO_HEADER_STYLE)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(15)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        title_row = QHBoxLayout()

        self.arrow_label = QLabel("▶")
        self.arrow_label.setFont(QFont("Arial", 10))
        self.arrow_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.arrow_label.setFixedWidth(20)
        title_row.addWidget(self.arrow_label)

        title = QLabel(self.scenario["name"])
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title.setWordWrap(True)
        title_row.addWidget(title)

        title_row.addStretch()

        diff_color = get_difficulty_color(self.scenario["difficulty"])
        diff_badge = QLabel(self.scenario["difficulty"])
        diff_badge.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        diff_badge.setStyleSheet(f"""
            background-color: {diff_color};
            color: white;
            padding: 4px 12px;
            border-radius: 10px;
        """)
        diff_badge.setFixedHeight(24)
        title_row.addWidget(diff_badge)

        info_layout.addLayout(title_row)

        desc = QLabel(self.scenario["description"])
        desc.setFont(QFont("Arial", 10))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 20px;")
        desc.setWordWrap(True)
        info_layout.addWidget(desc)

        header_layout.addLayout(info_layout)
        self.header.setLayout(header_layout)
        self.header.mousePressEvent = lambda e: self.toggle_expanded()

        self.main_layout.addWidget(self.header)

        # ── Expandable content ────────────────────────────────────────
        self.content_area = QFrame()
        self.content_area.setStyleSheet(SCENARIO_CONTENT_STYLE)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)

        settings_label = QLabel("Settings")
        settings_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        settings_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        content_layout.addWidget(settings_label)

        vm_label = QLabel("Virtual Machines")
        vm_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        vm_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        content_layout.addWidget(vm_label)

        for vm_name in self.scenario["vms"]:
            row = QHBoxLayout()
            lbl = QLabel(vm_name)
            lbl.setFont(QFont("Arial", 11))
            lbl.setStyleSheet("color: #cbd5e1;")
            row.addWidget(lbl)
            row.addStretch()
            content_layout.addLayout(row)

        self.content_area.setLayout(content_layout)
        self.content_area.hide()

        self.main_layout.addWidget(self.content_area)
        self.setLayout(self.main_layout)

    def toggle_expanded(self):
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.arrow_label.setText("▼")
            self.content_area.show()
            self.setStyleSheet(SCENARIO_ITEM_EXPANDED_STYLE)
            if self.parent_window:
                self.parent_window.show_scenario_vms(self.scenario)
        else:
            self.arrow_label.setText("▶")
            self.content_area.hide()
            self.setStyleSheet(SCENARIO_ITEM_STYLE)
            if self.parent_window:
                self.parent_window.clear_vm_area()