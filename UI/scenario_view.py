"""
Scenarios view with embedded VM display
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QFrame, QPushButton, QMessageBox,
                              QTabWidget, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from UI.widgets import ScenarioItem
from UI.vm_embed import VMEmbedWidget
from utils.styles import VM_DISPLAY_AREA_STYLE, COLORS


class ScenarioView(QWidget):
    def __init__(self, scenarios, vm_manager, user_data, parent=None):
        super().__init__(parent)
        self.scenarios = scenarios
        self.vm_manager = vm_manager
        self.user_data = user_data
        self.current_scenario = None
        self._embed_widgets: list[VMEmbedWidget] = []

        self.setup_ui()

        if not self.vm_manager.is_available():
            self._show_vbox_warning()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def setup_ui(self):
        main_container = QHBoxLayout()
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        # ── Left: scenario list ──────────────────────────────────────
        left_panel = QWidget()
        left_panel.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(30, 30, 15, 30)
        left_layout.setSpacing(20)

        header = QLabel("Scenarios")
        header.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(header)

        subtitle = QLabel("Select a scenario to view and control virtual machines")
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

        # ── Right: VM display ────────────────────────────────────────
        self.vm_display_area = QFrame()
        self.vm_display_area.setStyleSheet(VM_DISPLAY_AREA_STYLE)

        self.vm_area_layout = QVBoxLayout()
        self.vm_area_layout.setContentsMargins(20, 20, 20, 20)
        self.vm_area_layout.setSpacing(12)

        self._add_placeholder()

        self.vm_display_area.setLayout(self.vm_area_layout)
        main_container.addWidget(self.vm_display_area, stretch=3)

        self.setLayout(main_container)

    # ------------------------------------------------------------------
    # VM area management
    # ------------------------------------------------------------------

    def _add_placeholder(self):
        vm_header = QLabel("VM Display Area")
        vm_header.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        vm_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.vm_area_layout.addWidget(vm_header)

        placeholder = QLabel("Select and expand a scenario to launch virtual machines")
        placeholder.setFont(QFont('Arial', 12))
        placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vm_area_layout.addWidget(placeholder)
        self.vm_area_layout.addStretch()

    def _clear_vm_area(self):
        # Properly clean up embed widgets first
        for w in self._embed_widgets:
            w.deleteLater()
        self._embed_widgets.clear()

        while self.vm_area_layout.count():
            item = self.vm_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_scenario_vms(self, scenario):
        """Called when user expands a scenario — build the VM display panel."""
        self.current_scenario = scenario
        self._clear_vm_area()

        # Header row
        header = QLabel(scenario['name'])
        header.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.setWordWrap(True)
        self.vm_area_layout.addWidget(header)

        desc = QLabel(scenario['description'])
        desc.setFont(QFont('Arial', 11))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        self.vm_area_layout.addWidget(desc)

        if not self.vm_manager.is_available():
            warn = QLabel(
                "⚠️  VirtualBox / VBoxManage not found.\n"
                "Install VirtualBox and ensure VBoxManage is on your PATH."
            )
            warn.setFont(QFont('Arial', 10))
            warn.setStyleSheet(
                f"color: {COLORS['warning']};"
                f"background-color: {COLORS['bg_tertiary']};"
                "padding: 10px; border-radius: 6px;"
            )
            warn.setWordWrap(True)
            self.vm_area_layout.addWidget(warn)

        vms = scenario['vms']

        if len(vms) == 1:
            # Single VM: full-height embed
            embed = VMEmbedWidget(vms[0], self.vm_manager)
            self._embed_widgets.append(embed)
            self.vm_area_layout.addWidget(embed, stretch=1)

        else:
            # Multiple VMs: tabbed so each gets full space
            tabs = QTabWidget()
            tabs.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: 1px solid {COLORS['border']};
                    background-color: {COLORS['bg_primary']};
                }}
                QTabBar::tab {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_secondary']};
                    padding: 8px 18px;
                    border: 1px solid {COLORS['border']};
                    border-bottom: none;
                    border-radius: 4px 4px 0 0;
                }}
                QTabBar::tab:selected {{
                    background-color: {COLORS['accent_blue']};
                    color: white;
                }}
                QTabBar::tab:hover {{
                    background-color: {COLORS['bg_tertiary']};
                }}
            """)

            for vm_name in vms:
                embed = VMEmbedWidget(vm_name, self.vm_manager)
                self._embed_widgets.append(embed)
                tabs.addTab(embed, vm_name)

            self.vm_area_layout.addWidget(tabs, stretch=1)

    def clear_vm_area(self):
        self.current_scenario = None
        self._clear_vm_area()
        self._add_placeholder()

    # ------------------------------------------------------------------
    # VirtualBox warning
    # ------------------------------------------------------------------

    def _show_vbox_warning(self):
        QMessageBox.warning(
            self,
            "VirtualBox Not Found",
            "VBoxManage could not be found on this system.\n\n"
            "Please install VirtualBox (virtualbox.org) and make sure\n"
            "VBoxManage is available on your system PATH.\n\n"
            "VM controls will be visible but non-functional until VirtualBox is installed."
        )