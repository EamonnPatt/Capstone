"""
Scenarios view with VM display area and snapshot-aware launch
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QFrame, QPushButton, QMessageBox,
                              QProgressDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from UI.widgets import ScenarioItem, VMControl, VMWorker
from utils.styles import VM_DISPLAY_AREA_STYLE, LAUNCH_BUTTON_STYLE, COLORS


class ScenarioLaunchWorker(QThread):
    """
    Launches all VMs for a scenario in a background thread.
    Emits progress updates and a final all_done signal.
    """
    progress = pyqtSignal(str)                       # status text updates
    vm_done  = pyqtSignal(str, bool, str)            # (vm_name, success, message)
    all_done = pyqtSignal(list)                      # list of (vm_name, success, message)

    def __init__(self, vm_manager, scenario):
        super().__init__()
        self.vm_manager = vm_manager
        self.scenario = scenario

    def run(self):
        results = []
        snapshots = self.scenario.get('snapshots', {})

        for vm_name in self.scenario.get('vms', []):
            snapshot_name = snapshots.get(vm_name)

            if snapshot_name:
                self.progress.emit(f"Restoring snapshot for {vm_name}…")
            else:
                self.progress.emit(f"Starting {vm_name}…")

            success, message = self.vm_manager.launch_scenario_vm(vm_name, snapshot_name)
            results.append((vm_name, success, message))
            self.vm_done.emit(vm_name, success, message)

        self.all_done.emit(results)


class ScenarioView(QWidget):
    def __init__(self, scenarios, vm_manager, user_data, parent=None):
        super().__init__(parent)
        self.scenarios = scenarios
        self.vm_manager = vm_manager
        self.user_data = user_data
        self.current_scenario = None
        self._launch_worker = None

        self.setup_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def setup_ui(self):
        main_container = QHBoxLayout()
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        # ---- Left panel: scenario list ----
        left_panel = QWidget()
        left_panel.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(30, 30, 15, 30)
        left_layout.setSpacing(20)

        header = QLabel("Scenarios")
        header.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(header)

        subtitle = QLabel("Select a scenario to view settings and virtual machines")
        subtitle.setFont(QFont('Arial', 13))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)

        for scenario in self.scenarios:
            item = ScenarioItem(scenario, self.vm_manager, self)
            scroll_layout.addWidget(item)

        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)

        left_panel.setLayout(left_layout)
        main_container.addWidget(left_panel, stretch=2)

        # ---- Right panel: VM display area ----
        self.vm_display_area = QFrame()
        self.vm_display_area.setStyleSheet(VM_DISPLAY_AREA_STYLE)

        self.vm_area_layout = QVBoxLayout()
        self.vm_area_layout.setContentsMargins(30, 30, 30, 30)
        self.vm_area_layout.setSpacing(20)

        self._show_placeholder()

        self.vm_display_area.setLayout(self.vm_area_layout)
        main_container.addWidget(self.vm_display_area, stretch=3)

        self.setLayout(main_container)

    # ------------------------------------------------------------------
    # Placeholder / clear helpers
    # ------------------------------------------------------------------

    def _clear_vm_area(self):
        """Remove every widget from the VM area layout"""
        while self.vm_area_layout.count():
            item = self.vm_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_placeholder(self):
        vm_header = QLabel("VM Display Area")
        vm_header.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        vm_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.vm_area_layout.addWidget(vm_header)

        placeholder = QLabel("Select and expand a scenario to control virtual machines")
        placeholder.setFont(QFont('Arial', 12))
        placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vm_area_layout.addWidget(placeholder)
        self.vm_area_layout.addStretch()

    # ------------------------------------------------------------------
    # Scenario selected
    # ------------------------------------------------------------------

    def show_scenario_vms(self, scenario):
        """Populate the right panel when a scenario is expanded"""
        self.current_scenario = scenario
        self._clear_vm_area()

        # Scenario title
        header = QLabel(scenario['name'])
        header.setFont(QFont('Arial', 22, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.setWordWrap(True)
        self.vm_area_layout.addWidget(header)

        desc = QLabel(scenario['description'])
        desc.setFont(QFont('Arial', 12))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        self.vm_area_layout.addWidget(desc)

        # ---- Launch instructions box ----
        instructions_text = scenario.get('launch_instructions', '')
        if instructions_text:
            instr_frame = QFrame()
            instr_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_tertiary']};
                    border-radius: 8px;
                    border-left: 4px solid {COLORS['accent_blue']};
                }}
            """)
            instr_layout = QVBoxLayout()
            instr_layout.setContentsMargins(16, 12, 16, 12)
            instr_layout.setSpacing(6)

            instr_title = QLabel("📋  What you'll find when the VMs start")
            instr_title.setFont(QFont('Arial', 11, QFont.Weight.Bold))
            instr_title.setStyleSheet(f"color: {COLORS['accent_blue']};")
            instr_layout.addWidget(instr_title)

            instr_body = QLabel(instructions_text)
            instr_body.setFont(QFont('Courier', 10))
            instr_body.setStyleSheet(f"color: {COLORS['text_secondary']};")
            instr_body.setWordWrap(True)
            instr_layout.addWidget(instr_body)

            instr_frame.setLayout(instr_layout)
            self.vm_area_layout.addWidget(instr_frame)

        # ---- Snapshot status ----
        snapshots = scenario.get('snapshots', {})
        if snapshots:
            snap_frame = QFrame()
            snap_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_tertiary']};
                    border-radius: 8px;
                }}
            """)
            snap_layout = QVBoxLayout()
            snap_layout.setContentsMargins(16, 12, 16, 12)
            snap_layout.setSpacing(6)

            snap_title = QLabel("💾  Snapshots")
            snap_title.setFont(QFont('Arial', 11, QFont.Weight.Bold))
            snap_title.setStyleSheet(f"color: {COLORS['text_primary']};")
            snap_layout.addWidget(snap_title)

            for vm_name in scenario['vms']:
                snap_name = snapshots.get(vm_name, None)
                row = QHBoxLayout()

                vm_lbl = QLabel(vm_name)
                vm_lbl.setFont(QFont('Arial', 10))
                vm_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
                row.addWidget(vm_lbl)

                row.addStretch()

                if snap_name:
                    # Check whether the snapshot actually exists
                    exists = self.vm_manager.snapshot_exists(vm_name, snap_name)
                    if exists:
                        status_lbl = QLabel(f"✅  {snap_name}")
                        status_lbl.setStyleSheet(f"color: {COLORS['success']};")
                    else:
                        status_lbl = QLabel(f"⚠️  {snap_name}  (not found)")
                        status_lbl.setStyleSheet(f"color: {COLORS['warning']};")
                else:
                    status_lbl = QLabel("No snapshot — will start fresh")
                    status_lbl.setStyleSheet(f"color: {COLORS['text_tertiary']};")

                status_lbl.setFont(QFont('Arial', 10))
                row.addWidget(status_lbl)
                snap_layout.addLayout(row)

            snap_frame.setLayout(snap_layout)
            self.vm_area_layout.addWidget(snap_frame)

        # ---- VM controls (start / stop per VM) ----
        vm_section_label = QLabel("Virtual Machines")
        vm_section_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        vm_section_label.setStyleSheet(f"color: {COLORS['text_primary']}; margin-top: 10px;")
        self.vm_area_layout.addWidget(vm_section_label)

        for vm_name in scenario['vms']:
            vm_control = VMControl(vm_name, self.vm_manager)
            self.vm_area_layout.addWidget(vm_control)

        self.vm_area_layout.addStretch()

        # ---- Launch button ----
        self.launch_btn = QPushButton("🚀  Launch Scenario")
        self.launch_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        self.launch_btn.setStyleSheet(LAUNCH_BUTTON_STYLE)
        self.launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_btn.clicked.connect(lambda: self.launch_scenario(scenario))
        self.launch_btn.setMinimumHeight(52)
        self.vm_area_layout.addWidget(self.launch_btn)

    def clear_vm_area(self):
        """Restore the placeholder when a scenario is collapsed"""
        self.current_scenario = None
        self._clear_vm_area()
        self._show_placeholder()

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def launch_scenario(self, scenario):
        """
        Restore snapshots for each VM in the scenario, then start them.
        Runs in a background thread to keep the UI responsive.
        """
        # Confirmation dialog showing what will happen
        snapshots = scenario.get('snapshots', {})
        details_lines = []
        for vm_name in scenario['vms']:
            snap = snapshots.get(vm_name)
            if snap:
                details_lines.append(f"  • {vm_name}  →  restore snapshot '{snap}', then start")
            else:
                details_lines.append(f"  • {vm_name}  →  start (no snapshot configured)")

        details = "\n".join(details_lines)
        reply = QMessageBox.question(
            self,
            "Launch Scenario",
            f"Ready to launch: {scenario['name']}\n\n{details}\n\n"
            f"Any running VMs listed above will be force-powered off first.\n"
            f"Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Disable button to prevent double-clicks
        self.launch_btn.setEnabled(False)
        self.launch_btn.setText("Launching…")

        # Progress dialog
        self._progress = QProgressDialog(
            f"Launching {scenario['name']}…", None, 0, 0, self
        )
        self._progress.setWindowTitle("Launching Scenario")
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        # Background worker
        self._launch_worker = ScenarioLaunchWorker(self.vm_manager, scenario)
        self._launch_worker.progress.connect(self._on_launch_progress)
        self._launch_worker.all_done.connect(self._on_launch_done)
        self._launch_worker.start()

    def _on_launch_progress(self, message):
        if self._progress:
            self._progress.setLabelText(message)

    def _on_launch_done(self, results):
        # Close the progress dialog
        if self._progress:
            self._progress.close()
            self._progress = None

        # Re-enable the launch button
        self.launch_btn.setEnabled(True)
        self.launch_btn.setText("🚀  Launch Scenario")

        # Build a summary
        successes = [vm for vm, ok, _ in results if ok]
        failures  = [(vm, msg) for vm, ok, msg in results if not ok]

        if not failures:
            # All good
            scenario_name = self.current_scenario['name'] if self.current_scenario else "Scenario"
            instructions = (self.current_scenario or {}).get('launch_instructions', '')
            msg = f"All VMs launched successfully!\n\n"
            if instructions:
                msg += f"📋 What to expect:\n{instructions}"
            QMessageBox.information(self, f"{scenario_name} — Launched", msg)
        else:
            # At least one failure — show details
            fail_text = "\n\n".join(
                f"❌ {vm}:\n{msg}" for vm, msg in failures
            )
            ok_text = ""
            if successes:
                ok_text = "✅ Started: " + ", ".join(successes) + "\n\n"
            QMessageBox.warning(
                self,
                "Launch — Partial Failure",
                f"{ok_text}The following VMs could not be launched:\n\n{fail_text}"
            )