"""
Scenarios view with VM display area - Vagrant-integrated
"""

import threading

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QFrame, QPushButton, QMessageBox,
                              QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from UI.widgets import ScenarioItem, VagrantOutputDialog
from UI.vm_embed import VMEmbedWidget
from UI.vm_storage_dialog import VMStorageDialog
from utils.styles import VM_DISPLAY_AREA_STYLE, LAUNCH_BUTTON_STYLE, COLORS, SPLITTER_STYLE


class _RunningChecker(QThread):
    result = pyqtSignal(bool)   # True if any VM in the scenario is running

    def __init__(self, vm_manager, vm_names, vbox_names, parent=None):
        super().__init__(parent)
        self._vm_manager = vm_manager
        self._vm_names   = vm_names
        self._vbox_names = vbox_names

    def run(self):
        any_running = any(
            self._vm_manager.get_vm_state(self._vbox_names[vm]) == "running"
            for vm in self._vm_names
            if vm in self._vbox_names
        )
        self.result.emit(any_running)


class ScenarioView(QWidget):
    def __init__(self, scenarios, vm_manager, user_data,
                 vagrant_manager=None, parent=None):
        super().__init__(parent)
        self.scenarios        = scenarios
        self.vm_manager       = vm_manager
        self.user_data        = user_data
        self.vagrant_manager  = vagrant_manager
        self.current_scenario = None
        self.setup_ui()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(SPLITTER_STYLE)
        splitter.setHandleWidth(3)
        splitter.setChildrenCollapsible(False)

        # ── Left panel: scenario list ─────────────────────────────────
        left_panel = QWidget()
        left_panel.setMinimumWidth(260)
        left_panel.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 24, 16, 20)
        left_layout.setSpacing(12)

        header = QLabel("Scenarios")
        header.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(header)

        subtitle = QLabel("Select a scenario to get started")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 4, 0, 4)
        scroll_layout.setSpacing(10)

        for scenario in self.scenarios:
            item = ScenarioItem(
                scenario,
                self.vm_manager,
                vagrant_manager=self.vagrant_manager,
                parent=self,
            )
            scroll_layout.addWidget(item)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)

        # ── Right panel: VM display ───────────────────────────────────
        self.vm_display_area = QFrame()
        self.vm_display_area.setMinimumWidth(400)
        self.vm_display_area.setStyleSheet(VM_DISPLAY_AREA_STYLE)

        self.vm_area_layout = QVBoxLayout(self.vm_display_area)
        self.vm_area_layout.setContentsMargins(24, 24, 24, 24)
        self.vm_area_layout.setSpacing(14)

        self._show_placeholder()

        splitter.addWidget(left_panel)
        splitter.addWidget(self.vm_display_area)
        splitter.setSizes([320, 900])

        root.addWidget(splitter)

    def _clear_vm_area(self):
        while self.vm_area_layout.count():
            item = self.vm_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # remove any nested layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

    def _show_placeholder(self):
        self.vm_area_layout.addStretch()
        icon = QLabel("⬛")
        icon.setFont(QFont("Arial", 40))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"color: {COLORS['bg_tertiary']};")
        self.vm_area_layout.addWidget(icon)

        placeholder = QLabel("Select a scenario from the list\nto view and control its virtual machines")
        placeholder.setFont(QFont("Arial", 13))
        placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        self.vm_area_layout.addWidget(placeholder)
        self.vm_area_layout.addStretch()

    def show_scenario_vms(self, scenario):
        self.current_scenario = scenario
        self._clear_vm_area()

        header = QLabel(scenario["name"])
        header.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.setWordWrap(True)
        self.vm_area_layout.addWidget(header)

        desc = QLabel(scenario["description"])
        desc.setFont(QFont("Arial", 12))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        self.vm_area_layout.addWidget(desc)

        if self.vagrant_manager:
            vagrant_ok  = self.vagrant_manager.is_vagrant_installed()
            badge_text  = (self.vagrant_manager.get_vagrant_version()
                           if vagrant_ok else "Vagrant not found - install from vagrantup.com")
            badge_color = COLORS["success"] if vagrant_ok else COLORS["warning"]

            info_row = QHBoxLayout()

            badge = QLabel(badge_text)
            badge.setFont(QFont("Arial", 9))
            badge.setStyleSheet(f"color: {badge_color};")
            info_row.addWidget(badge)
            info_row.addStretch()

            from UI.vm_storage_dialog import get_vagrant_home
            storage_path = get_vagrant_home()
            storage_lbl = QLabel(f"Storage: {storage_path}" if storage_path else "Storage: not set")
            storage_lbl.setFont(QFont("Arial", 9))
            storage_lbl.setStyleSheet(f"color: {COLORS['text_tertiary']};")
            info_row.addWidget(storage_lbl)

            change_btn = QPushButton("Change")
            change_btn.setFont(QFont("Arial", 9))
            change_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            change_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['accent_blue']};
                    border: none;
                    padding: 0 4px;
                    text-decoration: underline;
                }}
                QPushButton:hover {{ color: {COLORS['text_primary']}; }}
            """)
            change_btn.clicked.connect(lambda: self._change_storage(scenario))
            info_row.addWidget(change_btn)

            self.vm_area_layout.addLayout(info_row)

        vm_section_label = QLabel("Virtual Machines")
        vm_section_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        vm_section_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; margin-top: 20px;"
        )
        self.vm_area_layout.addWidget(vm_section_label)

        vbox_names = scenario.get("vbox_names", {})
        if len(scenario["vms"]) > 1:
            # Resizable side-by-side splitter for multi-VM scenarios
            vm_splitter = QSplitter(Qt.Orientation.Horizontal)
            vm_splitter.setStyleSheet(SPLITTER_STYLE)
            vm_splitter.setHandleWidth(3)
            vm_splitter.setChildrenCollapsible(False)
            for vm_name in scenario["vms"]:
                embed = VMEmbedWidget(
                    display_name=vm_name,
                    vbox_name=vbox_names.get(vm_name, vm_name),
                    vm_manager=self.vm_manager,
                    vagrant_manager=self.vagrant_manager,
                    scenario_id=scenario["id"],
                    scenario=scenario,
                )
                vm_splitter.addWidget(embed)
            self.vm_area_layout.addWidget(vm_splitter, stretch=1)
        else:
            vm_name = scenario["vms"][0]
            embed = VMEmbedWidget(
                display_name=vm_name,
                vbox_name=vbox_names.get(vm_name, vm_name),
                vm_manager=self.vm_manager,
                vagrant_manager=self.vagrant_manager,
                scenario_id=scenario["id"],
                scenario=scenario,
            )
            self.vm_area_layout.addWidget(embed, stretch=1)

        self._launch_btn = QPushButton("Launch Scenario")
        self._launch_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._launch_btn.setStyleSheet(LAUNCH_BUTTON_STYLE)
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.clicked.connect(lambda: self.launch_scenario(scenario))
        self._launch_btn.setMinimumHeight(50)
        self.vm_area_layout.addWidget(self._launch_btn)

        self._launch_btn_scenario = scenario
        self._refresh_launch_btn()

        if not hasattr(self, '_launch_btn_timer'):
            from PyQt6.QtCore import QTimer
            self._launch_btn_timer = QTimer(self)
            self._launch_btn_timer.timeout.connect(self._refresh_launch_btn)
            self._launch_btn_timer.start(5000)

    def _refresh_launch_btn(self):
        if not hasattr(self, '_launch_btn') or not hasattr(self, '_launch_btn_scenario'):
            return
        scenario   = self._launch_btn_scenario
        vbox_names = scenario.get("vbox_names", {})
        vm_manager = self.vm_manager

        checker = _RunningChecker(vm_manager, scenario["vms"], vbox_names)
        checker.result.connect(self._apply_launch_btn_state)
        checker.start()
        # Keep a reference so it isn't GC'd before it finishes
        self._checker = checker

    def _apply_launch_btn_state(self, any_running: bool):
        if not hasattr(self, '_launch_btn'):
            return
        self._launch_btn.setEnabled(not any_running)
        self._launch_btn.setText("Scenario Running" if any_running else "Launch Scenario")

    def _change_storage(self, scenario):
        from UI.vm_storage_dialog import VMStorageDialog
        dlg = VMStorageDialog(scenario_name=scenario["name"], parent=self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            # Refresh the panel so the new path shows
            self.show_scenario_vms(scenario)

    def clear_vm_area(self):
        self.current_scenario = None
        if hasattr(self, '_launch_btn_timer'):
            self._launch_btn_timer.stop()
        self._launch_btn = None
        self._clear_vm_area()
        self._show_placeholder()

    def launch_scenario(self, scenario):
        reply = QMessageBox.question(
            self,
            "Launch Scenario",
            f"Start all VMs for '{scenario['name']}' now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        vbox_names = scenario.get('vbox_names', {})
        snapshots  = scenario.get('snapshots', {})

        # Check whether all VMs already exist in VirtualBox
        all_exist = all(
            self.vm_manager.vm_exists(vbox_names[vm])
            for vm in scenario["vms"]
            if vm in vbox_names
        )

        if all_exist:
            # Fast path: restore snapshots and start all VMs in background
            import threading

            def _launch_all():
                for vm_name in scenario["vms"]:
                    vbox_name     = vbox_names.get(vm_name)
                    snapshot_name = snapshots.get(vm_name)
                    if vbox_name:
                        # Skip snapshot restore if it hasn't been taken yet
                        if snapshot_name and not self.vm_manager.snapshot_exists(vbox_name, snapshot_name):
                            snapshot_name = None
                        success, msg = self.vm_manager.launch_scenario_vm(vbox_name, snapshot_name)
                        if not success:
                            print(f"[ScenarioView] Failed to launch {vm_name}: {msg}")

            threading.Thread(target=_launch_all, daemon=True).start()
        else:
            # Slow path: one or more VMs need first-time Vagrant provisioning
            if not self.vagrant_manager or not self.vagrant_manager.is_vagrant_installed():
                QMessageBox.information(
                    self, "Vagrant Not Found",
                    "Please install Vagrant from https://vagrantup.com then restart the app."
                )
                return

            if not VMStorageDialog.ensure_configured(self, scenario_name=scenario["name"]):
                return

            dlg = VagrantOutputDialog(
                f"Provisioning {scenario['name']} (first-time setup)", self
            )
            dlg.show()
            self.vagrant_manager.up_async(
                scenario["id"],
                vm_display_name=None,
                output_cb=lambda line: dlg.append_line(line),
                done_cb=lambda ok: dlg.mark_done(ok),
            )