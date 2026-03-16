"""
Reusable UI widgets
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QMessageBox, QApplication, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from utils.styles import (VM_CONTROL_STYLE, START_BUTTON_STYLE, STOP_BUTTON_STYLE,
                          SCENARIO_ITEM_STYLE, SCENARIO_ITEM_EXPANDED_STYLE,
                          SCENARIO_HEADER_STYLE, SCENARIO_CONTENT_STYLE, COLORS)
from core.data import get_difficulty_color


# ---------------------------------------------------------------------------
# Background worker — runs VM operations off the main thread so the UI
# doesn't freeze while VBoxManage is running.
# ---------------------------------------------------------------------------

class VMWorker(QThread):
    """Runs a VM operation in a background thread"""
    finished = pyqtSignal(bool, str)   # (success, message)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            # fn may return bool or (bool, str)
            if isinstance(result, tuple):
                self.finished.emit(result[0], result[1])
            else:
                self.finished.emit(bool(result), "")
        except Exception as e:
            self.finished.emit(False, str(e))


# ---------------------------------------------------------------------------
# VMControl — one row per VM in the right-hand panel
# ---------------------------------------------------------------------------

class VMControl(QFrame):
    """Individual VM control widget (start / stop / status)"""

    def __init__(self, vm_name, vm_manager, parent=None):
        super().__init__(parent)
        self.vm_name = vm_name
        self.vm_manager = vm_manager
        self._worker = None
        self.setup_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)
        self.update_status()

    def setup_ui(self):
        self.setStyleSheet(VM_CONTROL_STYLE)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)

        self.name_label = QLabel(self.vm_name)
        self.name_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.name_label)

        layout.addStretch()

        self.status_label = QLabel("Checking...")
        self.status_label.setFont(QFont('Arial', 10))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self.start_btn.setStyleSheet(START_BUTTON_STYLE)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_vm)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_vm)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)

    def update_status(self):
        state = self.vm_manager.get_vm_state(self.vm_name)
        if state == "running":
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        elif state == "poweroff":
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        elif state == "saved":
            self.status_label.setText("● Saved")
            self.status_label.setStyleSheet(f"color: {COLORS['accent_blue']}; font-weight: bold;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        elif state == "paused":
            self.status_label.setText("● Paused")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']}; font-weight: bold;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        else:
            self.status_label.setText("● Unknown")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

    def _set_busy(self, message):
        """Disable buttons and show interim status while a command runs"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def start_vm(self):
        self._set_busy("Starting…")
        self._worker = VMWorker(self.vm_manager.start_vm, self.vm_name, False)
        self._worker.finished.connect(self._on_start_done)
        self._worker.start()

    def _on_start_done(self, success, _msg):
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to start VM '{self.vm_name}'")
        self.update_status()

    def stop_vm(self):
        self._set_busy("Stopping…")
        self._worker = VMWorker(self.vm_manager.stop_vm, self.vm_name, False)
        self._worker.finished.connect(self._on_stop_done)
        self._worker.start()

    def _on_stop_done(self, success, _msg):
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to stop VM '{self.vm_name}'")
        self.update_status()


# ---------------------------------------------------------------------------
# ScenarioItem — expandable card in the left panel
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

        # ---- Header (clickable) ----
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

        # ---- Expandable content (Settings + VM list) ----
        self.content_area = QFrame()
        self.content_area.setStyleSheet(SCENARIO_CONTENT_STYLE)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(10)

        settings_label = QLabel("Settings")
        settings_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        settings_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        content_layout.addWidget(settings_label)

        vm_label = QLabel("Virtual Machines")
        vm_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        vm_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        content_layout.addWidget(vm_label)

        # Show each VM with its snapshot name if configured
        snapshots = self.scenario.get('snapshots', {})
        for vm_name in self.scenario['vms']:
            row = QHBoxLayout()

            vm_name_label = QLabel(f"  • {vm_name}")
            vm_name_label.setFont(QFont('Arial', 11))
            vm_name_label.setStyleSheet("color: #cbd5e1;")
            row.addWidget(vm_name_label)

            snap = snapshots.get(vm_name)
            if snap:
                snap_label = QLabel(f"snapshot: {snap}")
                snap_label.setFont(QFont('Arial', 9))
                snap_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
                row.addWidget(snap_label)

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