"""
Reusable UI widgets
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from utils.styles import (VM_CONTROL_STYLE, START_BUTTON_STYLE, STOP_BUTTON_STYLE,
                          SCENARIO_ITEM_STYLE, SCENARIO_ITEM_EXPANDED_STYLE,
                          SCENARIO_HEADER_STYLE, SCENARIO_CONTENT_STYLE, COLORS)
from core.data import get_difficulty_color


class VMControl(QFrame):
    """
    Individual VM control widget.
    All VBoxManage operations run in background threads – the UI never freezes.
    """

    def __init__(self, vm_name, vm_manager, parent=None):
        super().__init__(parent)
        self.vm_name = vm_name
        self.vm_manager = vm_manager
        self._busy = False
        self._active_worker = None
        self._active_pollers: list = []   # prevent pollers from being GC'd mid-run

        self.setup_ui()

        # Poll state every 5 seconds via a lightweight background thread
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_state)
        self._poll_timer.start(5000)

        # Immediate first check
        self._poll_state()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def setup_ui(self):
        self.setStyleSheet(VM_CONTROL_STYLE)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)

        # VM name
        self.name_label = QLabel(self.vm_name)
        self.name_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.name_label)

        layout.addStretch()

        # Headless toggle
        self.headless_check = QCheckBox("Headless")
        self.headless_check.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        self.headless_check.setToolTip("Run VM without a display window")
        layout.addWidget(self.headless_check)

        # Status indicator
        self.status_label = QLabel("● Checking...")
        self.status_label.setFont(QFont('Arial', 10))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)

        # Start button
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self.start_btn.setStyleSheet(START_BUTTON_STYLE)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._start_vm)
        layout.addWidget(self.start_btn)

        # Stop button
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_vm)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Cleanup – stop timer when widget is destroyed to avoid stale callbacks
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._stop_timer()
        super().closeEvent(event)

    def deleteLater(self):
        self._stop_timer()
        super().deleteLater()

    def _stop_timer(self):
        if self._poll_timer.isActive():
            self._poll_timer.stop()

    # ------------------------------------------------------------------
    # State polling (non-blocking)
    # ------------------------------------------------------------------

    def _poll_state(self):
        """Kick off an async state check. Result comes back via signal."""
        poller = self.vm_manager.poll_state_async(self.vm_name)
        self._active_pollers.append(poller)
        poller.state_ready.connect(self._apply_state)
        poller.state_ready.connect(lambda _: self._cleanup_poller(poller))
        poller.start()

    def _cleanup_poller(self, poller):
        try:
            self._active_pollers.remove(poller)
        except ValueError:
            pass

    def _apply_state(self, state: str):
        """Update UI labels and button states based on VM state string."""
        if state == "running":
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet(
                f"color: {COLORS['success']}; font-weight: bold;")
            self._set_buttons(start_enabled=False, stop_enabled=True)
        elif state in ("poweroff", "aborted"):
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self._set_buttons(start_enabled=True, stop_enabled=False)
        elif state in ("starting", "restoring"):
            self.status_label.setText("● Starting...")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self._set_buttons(start_enabled=False, stop_enabled=False)
        elif state == "paused":
            self.status_label.setText("● Paused")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self._set_buttons(start_enabled=False, stop_enabled=True)
        elif state == "saved":
            self.status_label.setText("● Saved")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self._set_buttons(start_enabled=True, stop_enabled=False)
        else:
            self.status_label.setText("● Unknown")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self._set_buttons(start_enabled=not self._busy, stop_enabled=not self._busy)

    def _set_buttons(self, start_enabled: bool, stop_enabled: bool):
        if not self._busy:
            self.start_btn.setEnabled(start_enabled)
            self.stop_btn.setEnabled(stop_enabled)

    # ------------------------------------------------------------------
    # Start / Stop actions (non-blocking)
    # ------------------------------------------------------------------

    def _start_vm(self):
        if self._busy:
            return
        self._set_busy(True, "Starting...")
        headless = self.headless_check.isChecked()
        worker = self.vm_manager.start_vm_async(self.vm_name, headless=headless)
        self._active_worker = worker
        worker.finished.connect(self._on_start_done)
        worker.finished.connect(lambda *_: setattr(self, '_active_worker', None))
        worker.start()

    def _on_start_done(self, success: bool, message: str):
        self._set_busy(False)
        if success:
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet(
                f"color: {COLORS['success']}; font-weight: bold;")
            self._set_buttons(start_enabled=False, stop_enabled=True)
        else:
            QMessageBox.critical(
                self, "Start Failed",
                f"Could not start '{self.vm_name}':\n\n{message}"
            )
            self._poll_state()   # refresh actual state

    def _stop_vm(self):
        if self._busy:
            return
        reply = QMessageBox.question(
            self, "Stop VM",
            f"Stop '{self.vm_name}'?\n\nChoose 'Yes' for graceful shutdown or 'No' to force power off.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return
        force = (reply == QMessageBox.StandardButton.No)
        self._set_busy(True, "Stopping...")
        worker = self.vm_manager.stop_vm_async(self.vm_name, force=force)
        self._active_worker = worker
        worker.finished.connect(self._on_stop_done)
        worker.finished.connect(lambda *_: setattr(self, '_active_worker', None))
        worker.start()

    def _on_stop_done(self, success: bool, message: str):
        self._set_busy(False)
        if success:
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self._set_buttons(start_enabled=True, stop_enabled=False)
        else:
            QMessageBox.critical(
                self, "Stop Failed",
                f"Could not stop '{self.vm_name}':\n\n{message}"
            )
            self._poll_state()

    def _set_busy(self, busy: bool, status_text: str = ""):
        self._busy = busy
        self.start_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(not busy)
        if status_text:
            self.status_label.setText(f"● {status_text}")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")

    # ------------------------------------------------------------------
    # Legacy – kept so anything that still calls update_status() doesn't crash
    # ------------------------------------------------------------------

    def update_status(self):
        self._poll_state()


# ---------------------------------------------------------------------------
# ScenarioItem – unchanged from original except minor cleanup
# ---------------------------------------------------------------------------

class ScenarioItem(QFrame):
    """Expandable scenario item"""

    def __init__(self, scenario, vm_manager, parent=None):
        super().__init__(parent)
        self.scenario = scenario
        self.vm_manager = vm_manager
        self.parent_window = parent
        self.is_expanded = False
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(SCENARIO_ITEM_STYLE)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header (clickable)
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
        self.arrow_label.setFont(QFont('Arial', 10))
        self.arrow_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.arrow_label.setFixedWidth(20)
        title_row.addWidget(self.arrow_label)

        title = QLabel(self.scenario['name'])
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title.setWordWrap(True)
        title_row.addWidget(title)

        title_row.addStretch()

        diff_color = get_difficulty_color(self.scenario['difficulty'])
        diff_badge = QLabel(self.scenario['difficulty'])
        diff_badge.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        diff_badge.setStyleSheet(f"""
            background-color: {diff_color};
            color: white;
            padding: 4px 12px;
            border-radius: 10px;
        """)
        diff_badge.setFixedHeight(24)
        title_row.addWidget(diff_badge)

        info_layout.addLayout(title_row)

        desc = QLabel(self.scenario['description'])
        desc.setFont(QFont('Arial', 10))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 20px;")
        desc.setWordWrap(True)
        info_layout.addWidget(desc)

        header_layout.addLayout(info_layout)
        self.header.setLayout(header_layout)
        self.header.mousePressEvent = lambda e: self.toggle_expanded()

        self.main_layout.addWidget(self.header)

        # Expandable content area
        self.content_area = QFrame()
        self.content_area.setStyleSheet(SCENARIO_CONTENT_STYLE)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)

        settings_label = QLabel("Settings")
        settings_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        settings_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        content_layout.addWidget(settings_label)

        vm_label = QLabel("VM")
        vm_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        vm_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        content_layout.addWidget(vm_label)

        for vm_name in self.scenario['vms']:
            vm_item_layout = QHBoxLayout()
            vm_name_label = QLabel(vm_name)
            vm_name_label.setFont(QFont('Arial', 11))
            vm_name_label.setStyleSheet("color: #cbd5e1;")
            vm_item_layout.addWidget(vm_name_label)
            vm_item_layout.addStretch()
            content_layout.addLayout(vm_item_layout)

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